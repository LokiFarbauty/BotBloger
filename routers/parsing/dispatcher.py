'''Этот модуль содержит глобальные объекты - диспетчер парсеров.
Он отвечает за автоматическую подгрузку парсеров из папки parsers.
Парсеры подгружаются при создании объекта ParserDispatcher и дальше хранятся в нем'''

# routers
from routers.parsing.parsing_dispatсher import ParserDispatcher, ASTaskStatus
from routers.logers import parsers_loger, app_loger
from routers.parsing.analyzer import analyze_posts, AnalyzerParams
from routers.parsing.interface_parser import ParserInterface, ParseParams, ParserInterfaceReturns, APost
from routers.parsing.parsing_config import PARSE_VK_POST_NUM, PARSE_VK_MAX_TEXT_LEN

# models
from models.data_model import get_elements
from models.data.parse_task import ParseTask, ParseTaskStates, ParseTaskActive
from models.data.parser import Parser
from models.data.post import Post
from models.saver import save_posts

# py
import asyncio
import aiohttp
from tqdm import tqdm
import enum

# const
INFINITE = 'all'


parsing_dispatcher = ParserDispatcher(parsers_loger)

class ParsingMode(enum.Enum):
    ARCHIVE = 'архив' # не указан период - количество постов INFINITE
    UPDATE_SINGLE = 'разовое обновление' # не указан период - количество постов 0
    UPDATE_PERIOD = 'периодическое обновление' # указан период - количество постов 0
    COUNT = 'заданное количество' # не указан период - задано количество постов
    UNKNOWN = 'не определн'  # в противном случае

async def refresh_task_state(task: ParseTask, state, error = None):
    try:
        task.state = state
        task.error = error
        task.save()
    except:
        pass

async def get_post_count_in_VK_source(task: ParseTask):
    try:
        post_count = 1
        group_info = None
        token = task.parser.token
        parser = parsing_dispatcher.get_parser(task.parser.platform)
        if parser != None:
            params = ParseParams(target_id=task.target_id, target_type=task.target_type, token=token, post_count=1,
                                 filter=task.filter, use_free_proxy=False)
            group_info = await parser.get_vk_wall(params)
        if group_info == None:
            parsers_loger.error(
                f'get_post_count_in_VK_source(task={task.get_id()}). Ошибка: не удалось получить информацию о ВК объекте: '
                f'{task.target_type} "{task.target_name}" (id: {task.target_id})')
            return 0
        post_count = group_info[0]['response']['count']
        return post_count
    except Exception as ex:
        parsers_loger.error(
            f'get_post_count_in_VK_source(task={task.get_id()}). Ошибка: {ex}')
        return 0

async def parsing(task: ParseTask, show_progress = True):
    try:
        task.state = ParseTaskStates.InWork.value
        task.error = None
        task.save()
        token = task.parser.token
        parser = parsing_dispatcher.get_parser(task.parser.platform)
        post_num = PARSE_VK_POST_NUM
        if task.post_num != INFINITE:
            if (task.post_num<PARSE_VK_POST_NUM) and (task.post_num>0):
                post_num = task.post_num
        params = ParseParams(target_id=task.target_id, target_type=task.target_type, token=token, post_count=post_num,
                             filter=task.filter,
                             use_free_proxy=False)
        period = task.period
        while True:
            # Определяем счетчики
            got_post_num = 0
            # Задаем режим
            if (task.post_num == INFINITE) and ((task.period == 0) or (task.period == None)):
                parsing_mode = ParsingMode.ARCHIVE
                last_post_id = 0
                source_post_count = await get_post_count_in_VK_source(task)
            elif (task.post_num == 0) and ((task.period == 0) or (task.period == None)):
                parsing_mode = ParsingMode.UPDATE_SINGLE
                last_post_id = task.last_post_id
                source_post_count = await get_post_count_in_VK_source(task)
            elif (task.post_num > 0) and ((task.period == 0) or (task.period == None)):
                parsing_mode = ParsingMode.COUNT
                last_post_id = 0
                source_post_count = task.post_num
            elif (task.post_num == 0) and (task.period > 0):
                parsing_mode = ParsingMode.UPDATE_PERIOD
                last_post_id = task.last_post_id
                source_post_count = await get_post_count_in_VK_source(task)
            else:
                parsing_mode = ParsingMode.UNKNOWN
                last_post_id = 0
                source_post_count = 0
                task.state = ParseTaskStates.Error
                task.error = 'Не определен режим парсинга. Настройте правильно период.'
                task.save()
                return task.state
            # if show_progress:
            #     rng = tqdm(range(0, source_post_count, post_num), colour='green', desc='Выгружаем данные')
            # else:
            #     rng = range(0, source_post_count, post_num)
            #rng = range(0, source_post_count, post_num)
            last_post_id_saved = False
            end_parse = False
            # Цикл парсинга
            #for posts_got in rng:
            posts_got = 0
            while posts_got<source_post_count:
                if end_parse:
                    # Если установлен флаг прекращения парсинга останавливаемся
                    #print(f'Выполнение задачи "{task.name}" завершено. Загружено {got_post_num} постов.')
                    break
                # Парсим
                params.offset = posts_got
                conn = aiohttp.TCPConnector(limit=None, ttl_dns_cache=300)
                async with aiohttp.ClientSession(connector=conn) as new_session:
                    parse_res = await parser.parse(params, session=new_session)
                # Если ничего не спарсили дальше не парсим
                if type(parse_res) is not list:
                    # Ошибка при получении данных из ВК
                    parsers_loger.error(f'При выполнение задачи "{task.name}" произошла ошибка: {parse_res}')
                    #print(f'Выполнение задачи "{task.name}" завершено. Загружено {got_post_num} постов.')
                    break
                if parse_res == []:
                    # Ничего не спарсили
                    break
                # Подготовка параметров
                if task.criterion.post_min_text_length==None:
                    min_text_len = 0
                else:
                    min_text_len = task.criterion.post_min_text_length
                if task.criterion.post_max_text_length==None:
                    max_text_len = PARSE_VK_MAX_TEXT_LEN
                else:
                    max_text_len = task.criterion.post_min_text_length
                # Проверяем есть ли среди постов last_post_id и отрезаем все, что за ним
                # У первого спарсеного поста будет максимальный post_id и если он уже ессть в базе то то что за ним точно есть
                if parsing_mode == ParsingMode.UPDATE_PERIOD or parsing_mode == ParsingMode.UPDATE_SINGLE:
                    try:
                        # Ищем в пуле постов пост_ид который меньше заданного, если находим то отрезаем всё что после него, если не находим парсим дальше и устанавливаем флаг прекращения.
                        for el in parse_res:
                            if el.post_id <= last_post_id:
                                end_parse = True
                                break
                        # max_post_id = parse_res[0].post_id
                        # tmp_post = Post.get_post(post_id=max_post_id, task_id=task, source_id=task.target_id)
                        # if tmp_post != None:
                        #     end_parse = True
                    except Exception as ex:
                        continue
                # Анализ
                state = 'анализ'
                anl_params = AnalyzerParams(task_id=task.get_id(), target_id=task.target_id, min_text_len=min_text_len, max_text_len=max_text_len,
                                        key_words=task.criterion.key_words, hashtags=task.criterion.hashtags, clear_words=task.criterion.clear_words,
                                        forbidden_words=task.criterion.forbidden_words, post_start_date=task.criterion.post_start_date, post_end_date=task.criterion.post_end_date,
                                        last_post_id=last_post_id, video_platform=task.criterion.video_platform)
                proc_posts = await analyze_posts(parse_res, anl_params)
                # if len(proc_posts) == 0:
                #     reas = f'В анализируемом пуле из {post_num} постов при выполнении задачи "{task.name}" (key: {task.get_id()}) не найдено ни одного подходящего под критерии поста. Задача остановлена.'
                #     print(reas)
                #     parsers_loger.warning(reas)
                #     break # Если ничего подходящего в 100 записях нет, дальше можно не искать
                state = 'сохранение'
                if not last_post_id_saved and proc_posts != []:
                    try:
                        task.last_post_id = proc_posts[0].post_id
                        task.save()
                        last_post_id_saved = True
                    except:
                        pass
                await save_posts(proc_posts, task.target_id, task=task, program=task.program)
                #
                got_post_num = got_post_num + len(proc_posts)
                posts_got=posts_got+post_num
                #
            if parsing_mode != ParsingMode.UPDATE_PERIOD:
                print(f'Выполнение задачи "{task.name}" завершено. Загружено {got_post_num} постов.')
                # Сохраняем состояние
                await refresh_task_state(task, ParseTaskStates.Ended.value)
                break
            # Обновляем данные задачи
            task = ParseTask.get_by_id(task.get_id())
            # Сохраняем состояние
            await refresh_task_state(task, ParseTaskStates.InWork.value)
            await asyncio.sleep(period)
    except Exception as ex:
        await refresh_task_state(task, ParseTaskStates.Error.value, ex)
        err_str = f'При выполнении задачи {task.name} (key: {task.get_id()}) произошла ошибка: {ex}. Задача остановлена.'
        parsers_loger.error(err_str)


async def init_tasks():
    # Получаем список задач из базы
    tasks = get_elements(ParseTask)
    task_num = 0
    for task in tasks:
        # Настраиваем
        try:
            if task.active == ParseTaskActive.InWork.value:
                parsing_dispatcher.tasks.append(asyncio.create_task(parsing(task), name=task.name))
                task_num += 1
        except Exception as ex:
            print(f'При запуске задачи {task.name} (key: {task.get_id()}) возникла ошибка: {ex}')
            parsers_loger.error(f'При запуске задачи {task.name} (key: {task.get_id()}) возникла ошибка: {ex}')
            continue
    app_loger.info(f'Запущено {task_num} задач.')
    print(f'Запущено {task_num} задач.')
    return 0