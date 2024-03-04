

# routers
from routers.logers import parsers_loger, app_loger
from routers.parsing.analyzer import analyze_posts, AnalyzerParams
from routers.parsing.interface_parser import ParserInterface, ParseParams, ParserInterfaceReturns, APost
from routers.parsing.parsing_config import PARSE_VK_POST_NUM, PARSE_VK_MAX_TEXT_LEN
from routers.parsing.rating import refresh_avg_rating

# models
from models.data.parse_task import ParseTask, ParseTaskStates, ParseTaskActive, ParseModes
from models.saver import save_posts
from models.data.post import Post, ModerateStates

# py
import asyncio
import aiohttp
from tqdm import tqdm
import enum
import random
from datetime import datetime

# const
INFINITE = 'all'

# class ParsingMode(enum.Enum):
#     ARCHIVE = 'архив' # не указан период - количество постов INFINITE
#     UPDATE_SINGLE = 'разовое обновление' # не указан период - количество постов 0
#     UPDATE_PERIOD = 'периодическое обновление' # указан период - количество постов 0
#     COUNT = 'заданное количество' # не указан период - задано количество постов
#     UNKNOWN = 'не определн'  # в противном случае


async def get_post_count_in_VK_source(parser: ParserInterface, task: ParseTask):
    try:
        post_count = 1
        group_info = None
        token = task.parser.token
        #parser = parsing_dispatcher.get_parser(task.parser.platform)
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

#async def parsing(task: ParseTask, parser: ParserInterface, quick_start = False, infinite_def = INFINITE):

async def arhive_parsing_process(task: ParseTask, parser, params: ParseParams, source_post_count: int, last_post_id: int, post_num = 50, debug = False):
    last_post_id_saved = False
    try:
        posts_remains = int(task.posts_remains)
        if posts_remains > source_post_count:
            parsers_loger.info(f'Архивный парсинг задачи <{task.name}> остановлен. Все посты уже загружены.')
            print(f'Архивный парсинг задачи <{task.name}> остановлен. Все посты уже загружены.')
            return
        for posts_got in tqdm(range(posts_remains, source_post_count, post_num), colour='green', desc='Выгружаем данные'):
            # Парсим
            if debug:
                parsers_loger.info(f'Новый цикл парсинга <{task.name}>. Постов скачано: {posts_got} из {source_post_count}')
                print(f'Новый цикл парсинга <{task.name}>. Постов скачано: {posts_got} из {source_post_count}')
            #
            params.offset = posts_got
            conn = aiohttp.TCPConnector(limit=None, ttl_dns_cache=300)
            async with aiohttp.ClientSession(connector=conn) as new_session:
                parse_res = await parser.parse(params, session=new_session)
            # Если ничего не спарсили дальше не парсим
            if type(parse_res) is not list or parse_res == []:
                # Ошибка при получении данных из ВК
                task.posts_remains = posts_got-post_num
                task.save()
                parsers_loger.error(f'При выполнение парсинга "{task.name}" произошла ошибка: {parse_res} (break)')
                print(f'При выполнение архивного парсинга "{task.name}" произошла ошибка: {parse_res}. При возобновлении будут получены оставшиеся посты.')
                # print(f'При выполнение задачи "{task.name}" произошла ошибка: парсер не вернул данные (break).'
                # print(f'Выполнение задачи "{task.name}" завершено. Загружено {got_post_num} постов.')
                break
            # Подготовка параметров
            if task.criterion.post_min_text_length == None:
                min_text_len = 0
            else:
                min_text_len = task.criterion.post_min_text_length
            if task.criterion.post_max_text_length == None:
                max_text_len = PARSE_VK_MAX_TEXT_LEN
            else:
                max_text_len = task.criterion.post_max_text_length
            # Анализ
            if posts_got > 678*50:
                pass
            state = 'анализ'
            anl_params = AnalyzerParams(task_id=task.get_id(), target_id=task.target_id, min_text_len=min_text_len,
                                        max_text_len=max_text_len,
                                        key_words=task.criterion.key_words, hashtags=task.criterion.hashtags,
                                        clear_words=task.criterion.clear_words, replace_words=task.criterion.replace_words,
                                        forbidden_words=task.criterion.forbidden_words,
                                        post_start_date=task.criterion.post_start_date,
                                        post_end_date=task.criterion.post_end_date,
                                        last_post_id=last_post_id, video_platform=task.criterion.video_platform,
                                        del_hashtags=task.criterion.del_hashtags,
                                        url_action=task.criterion.url_action, min_rate=task.criterion.min_rate)
            proc_posts = await analyze_posts(parse_res, anl_params)
            state = 'сохранение'
            if not last_post_id_saved and proc_posts != []:
                try:
                    task.last_post_id = proc_posts[0].post_id
                    task.save()
                    last_post_id_saved = True
                except:
                    pass
            await save_posts(proc_posts, task.target_id, task=task, program=task.program)
            task.posts_remains = posts_got
            task.save()
            #
        #task.posts_remains = source_post_count
        #task.save()
        await refresh_avg_rating(task)
    except Exception as ex:
        print(f'При выполнении задачи "{task.name}" произошла ошибка: "{ex}". Задача остановлена.')
        parsers_loger.error(f'При выполнении задачи "{task.name}" произошла ошибка: "{ex}". Задача остановлена.')

async def period_parsing_process(task: ParseTask, parser, parsing_mode, params: ParseParams, source_post_count: int, last_post_id: int, post_num = 50, debug = False):
    '''Субпроцесс парсинга когда требуется парсить периодически'''
    posts_got = 0
    got_post_num = 0
    last_post_id_saved = False
    end_parse = False
    # task_id = task.get_id
    # if task_id == 7:
    #     pass
    while posts_got < source_post_count:
        #
        # if posts_got>5150:
        #     pass
        #
        if end_parse:
            # Обновляем рейтинги
            await refresh_avg_rating(task)
            # Если установлен флаг прекращения парсинга останавливаемся
            # print(f'Выполнение задачи "{task.name}" завершено. Загружено {got_post_num} постов.')
            if debug: parsers_loger.info(
                f'Выполнение задачи <{task.name}> прекращено командой <break>. Загружено {got_post_num} постов.')
            break
        # Парсим
        if debug:
            parsers_loger.info(f'Новый цикл парсинга <{task.name}>. Постов скачано: {posts_got} из {source_post_count}')
            print(f'Новый цикл парсинга <{task.name}>. Постов скачано: {posts_got} из {source_post_count}')
        params.offset = posts_got
        conn = aiohttp.TCPConnector(limit=None, ttl_dns_cache=300)
        async with aiohttp.ClientSession(connector=conn) as new_session:
            parse_res = await parser.parse(params, session=new_session)
        # Если ничего не спарсили дальше не парсим
        if type(parse_res) is not list:
            # Ошибка при получении данных из ВК
            parsers_loger.error(f'При выполнение задачи "{task.name}" произошла ошибка: {parse_res} (break)')
            # print(f'Выполнение задачи "{task.name}" завершено. Загружено {got_post_num} постов.')
            break
        if parse_res == []:
            # Ничего не спарсили
            break
        # Подготовка параметров
        if task.criterion.post_min_text_length == None:
            min_text_len = 0
        else:
            min_text_len = task.criterion.post_min_text_length
        if task.criterion.post_max_text_length == None:
            max_text_len = PARSE_VK_MAX_TEXT_LEN
        else:
            max_text_len = task.criterion.post_max_text_length
        # Проверяем есть ли среди постов last_post_id и отрезаем все, что за ним
        # У первого спарсеного поста будет максимальный post_id и если он уже ессть в базе то то что за ним точно есть
        if parsing_mode == ParseModes.UPDATE_PERIOD.value or parsing_mode == ParseModes.UPDATE_SINGLE.value:
            try:
                # Ищем в пуле постов пост_ид который меньше заданного, если находим то отрезаем всё что после него, если не находим парсим дальше и устанавливаем флаг прекращения.
                if last_post_id != 0:
                    cut_pos = len(parse_res)
                    for i, el in enumerate(parse_res, start=0):
                        # Проверяем последний id
                        if el.post_id <= last_post_id:
                            cut_pos = i
                            end_parse = True
                            break
                    # Обрезаем лишние посты
                    parse_res = parse_res[:cut_pos]
                # Проверяем дату поста
                if task.criterion.post_start_date != 0:
                    cut_pos = len(parse_res)
                    for i, el in enumerate(parse_res, start=0):
                        if task.criterion.post_start_date > el.dt:
                            cut_pos = i
                            end_parse = True
                            break
                    # Обрезаем лишние посты
                    parse_res = parse_res[:cut_pos]
                if task.criterion.post_end_date != 0:
                    cut_pos = len(parse_res)
                    for i, el in enumerate(parse_res, start=0):
                        if task.criterion.post_end_date < el.dt:
                            cut_pos = i
                            end_parse = True
                            break
                    # Обрезаем лишние посты
                    parse_res = parse_res[cut_pos:]
                # max_post_id = parse_res[0].post_id
                # tmp_post = Post.get_post(post_id=max_post_id, task_id=task, source_id=task.target_id)
                # if tmp_post != None:
                #     end_parse = True
            except Exception as ex:
                continue
        # Анализ
        state = 'анализ'
        anl_params = AnalyzerParams(task_id=task.get_id(), target_id=task.target_id, min_text_len=min_text_len,
                                    max_text_len=max_text_len,
                                    key_words=task.criterion.key_words, hashtags=task.criterion.hashtags,
                                    clear_words=task.criterion.clear_words, replace_words=task.criterion.replace_words,
                                    forbidden_words=task.criterion.forbidden_words,
                                    post_start_date=task.criterion.post_start_date,
                                    post_end_date=task.criterion.post_end_date,
                                    last_post_id=last_post_id, video_platform=task.criterion.video_platform,
                                    del_hashtags=task.criterion.del_hashtags,
                                    url_action=task.criterion.url_action, min_rate=task.criterion.min_rate)
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
        posts_got = posts_got + post_num

async def parsing(**_kwargs):
    '''
    Функуия выполняет полный цикл парсинга:
    - получение постов парсером
    - анализ, полученных постов
    - сохранение подходящих постов

    Args:
        task (): модель задачи из базы
        parser (): парсер
        quick_start (): если установлено, то задача запускается без задержки
        infinite_def (): обозначение бесконечного количества постов для парсинга стандартно - all

    Returns:

    '''
    try:
        debug = False
        # Получаем параметры
        par_task = _kwargs['task']
        quick_start = _kwargs['quick_start']
        infinite_def = _kwargs['infinite_def']
        parser = _kwargs['parser']
        # Ждем немного
        if par_task.moderated == 0:
            delay = random.randrange(start=120, stop=3600)
        else:
            delay = 1
            delay = random.randrange(start=30, stop=300)
        delay=1
        if debug: parsers_loger.info(f'Выполнение задачи <{par_task.name}> начнётся через {delay/60} мин.')
        if not quick_start: await asyncio.sleep(delay)
        #
        par_task.state = ParseTaskStates.InWork.value
        par_task.error = None
        par_task.save()
        # token = par_task.parser.token
        # post_num = PARSE_VK_POST_NUM
        # if par_task.post_num != infinite_def:
        #     if (par_task.post_num<PARSE_VK_POST_NUM) and (par_task.post_num>0):
        #         post_num = par_task.post_num
        # params = ParseParams(target_id=par_task.target_id, target_type=par_task.target_type, token=token, post_count=post_num,
        #                      filter=par_task.filter, use_free_proxy=False)
        # period = par_task.period
        # Определяем режим парсинга
        parse_mode = par_task.mode
        while True:
            # Проверяем что задача еще существует
            task = ParseTask.get_task(key=par_task.get_id())
            if task == None:
                parsers_loger.critical(f'Задача "{par_task.name}" не найдена. Процесс выполнения задачи прерван.')
                return
            # Проверяем время
            if not quick_start:
                cur_time = datetime.now().time().hour
                if cur_time < task.start_parse_hour or cur_time > task.end_parse_hour:
                    # Ждем 20 минут
                    await asyncio.sleep(1200)
                    continue
            # Проверяем не превышен ли лимит постов на премодерации
            period = task.period
            if task.moderated == 1:
                not_processed_posts = Post.select().where((Post.parse_task == task) & (Post.moderate == ModerateStates.NotVerified.value)).count()
                if not_processed_posts >= task.max_not_moderated_posts:
                    await asyncio.sleep(period)
                    continue
            #
            token = task.parser.token
            post_num = PARSE_VK_POST_NUM
            if task.post_num != infinite_def:
                if (task.post_num < PARSE_VK_POST_NUM) and (task.post_num > 0):
                    post_num = task.post_num
            params = ParseParams(target_id=task.target_id, target_type=task.target_type, token=token,
                                 post_count=post_num,
                                 filter=task.filter, use_free_proxy=False)
            # Определяем счетчики
            task_post_num = task.post_num
            if task_post_num == 'all':
                task_post_num = 0
            got_post_num = 0
            # Задаем режим
            parsing_mode = task.mode
            if parsing_mode == ParseModes.ARCHIVE.value:
                last_post_id = 0
                source_post_count = await get_post_count_in_VK_source(parser, task)
            elif parsing_mode == ParseModes.UPDATE_SINGLE.value:
                last_post_id = task.last_post_id
                source_post_count = await get_post_count_in_VK_source(parser, task)
            elif parsing_mode == ParseModes.COUNT.value:
                last_post_id = 0
                source_post_count = task_post_num
            elif parsing_mode == ParseModes.UPDATE_PERIOD.value:
                last_post_id = task.last_post_id
                source_post_count = await get_post_count_in_VK_source(parser, task)
            else:
                parsing_mode = ParseModes.UNKNOWN.value
                task.state = ParseTaskStates.Error
                task.error = 'Не определен режим парсинга. Настройте правильно период.'
                task.save()
                return task.state
            # if (task_post_num == INFINITE) and ((task.period == 0) or (task.period == None)):
            #     parsing_mode = ParsingMode.ARCHIVE
            #     last_post_id = 0
            #     source_post_count = await get_post_count_in_VK_source(parser, task)
            # elif (task_post_num == 0) and ((task.period == 0) or (task.period == None)):
            #     parsing_mode = ParsingMode.UPDATE_SINGLE
            #     last_post_id = task.last_post_id
            #     source_post_count = await get_post_count_in_VK_source(parser, task)
            # elif (task_post_num > 0) and ((task.period == 0) or (task.period == None)):
            #     parsing_mode = ParsingMode.COUNT
            #     last_post_id = 0
            #     source_post_count = task_post_num
            # elif (task_post_num == 0) and (task.period > 0):
            #     parsing_mode = ParsingMode.UPDATE_PERIOD
            #     last_post_id = task.last_post_id
            #     source_post_count = await get_post_count_in_VK_source(parser, task)
            # else:
            #     parsing_mode = ParsingMode.UNKNOWN
            #     last_post_id = 0
            #     source_post_count = 0
            #     task.state = ParseTaskStates.Error
            #     task.error = 'Не определен режим парсинга. Настройте правильно период.'
            #     task.save()
            #     return task.state
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
            got_post_num = 0
            if debug: parsers_loger.info(f'Начато выполнение задачи <{task.name}>.')
            if parsing_mode != ParseModes.ARCHIVE.value:
                await period_parsing_process(task=task, parser=parser, parsing_mode=parsing_mode, params=params,
                                         source_post_count=source_post_count, last_post_id=last_post_id,
                                         post_num=post_num, debug=debug)
            else:
                await arhive_parsing_process(task=task, parser=parser, params=params,
                                         source_post_count=source_post_count, last_post_id=last_post_id,
                                         post_num=post_num, debug=debug)
            # while posts_got < source_post_count:
            #     #
            #     # if posts_got>5150:
            #     #     pass
            #     #
            #     if end_parse:
            #         # Обновляем рейтинги
            #         await refresh_avg_rating(task)
            #         # Если установлен флаг прекращения парсинга останавливаемся
            #         #print(f'Выполнение задачи "{task.name}" завершено. Загружено {got_post_num} постов.')
            #         if debug: parsers_loger.info(f'Выполнение задачи <{task.name}> прекращено командой <break>. Загружено {got_post_num} постов.')
            #         break
            #     # Парсим
            #     if debug:
            #         parsers_loger.info(f'Новый цикл парсинга <{task.name}>. Постов скачано: {posts_got} из {source_post_count}')
            #         print(f'Новый цикл парсинга <{task.name}>. Постов скачано: {posts_got} из {source_post_count}')
            #     params.offset = posts_got
            #     conn = aiohttp.TCPConnector(limit=None, ttl_dns_cache=300)
            #     async with aiohttp.ClientSession(connector=conn) as new_session:
            #         parse_res = await parser.parse(params, session=new_session)
            #     # Если ничего не спарсили дальше не парсим
            #     if type(parse_res) is not list:
            #         # Ошибка при получении данных из ВК
            #         parsers_loger.error(f'При выполнение задачи "{task.name}" произошла ошибка: {parse_res} (break)')
            #         #print(f'Выполнение задачи "{task.name}" завершено. Загружено {got_post_num} постов.')
            #         break
            #     if parse_res == []:
            #         # Ничего не спарсили
            #         break
            #     # Подготовка параметров
            #     if task.criterion.post_min_text_length==None:
            #         min_text_len = 0
            #     else:
            #         min_text_len = task.criterion.post_min_text_length
            #     if task.criterion.post_max_text_length==None:
            #         max_text_len = PARSE_VK_MAX_TEXT_LEN
            #     else:
            #         max_text_len = task.criterion.post_max_text_length
            #     # Проверяем есть ли среди постов last_post_id и отрезаем все, что за ним
            #     # У первого спарсеного поста будет максимальный post_id и если он уже ессть в базе то то что за ним точно есть
            #     if parsing_mode == ParsingMode.UPDATE_PERIOD or parsing_mode == ParsingMode.UPDATE_SINGLE:
            #         try:
            #             # Ищем в пуле постов пост_ид который меньше заданного, если находим то отрезаем всё что после него, если не находим парсим дальше и устанавливаем флаг прекращения.
            #             if last_post_id != 0:
            #                 cut_pos = len(parse_res)
            #                 for i, el in enumerate(parse_res, start=0):
            #                     # Проверяем последний id
            #                     if el.post_id <= last_post_id:
            #                         cut_pos = i
            #                         end_parse = True
            #                         break
            #                 # Обрезаем лишние посты
            #                 parse_res = parse_res[:cut_pos]
            #             # Проверяем дату поста
            #             if task.criterion.post_start_date != 0:
            #                 cut_pos = len(parse_res)
            #                 for i, el in enumerate(parse_res, start=0):
            #                     if task.criterion.post_start_date > el.dt:
            #                         cut_pos = i
            #                         end_parse = True
            #                         break
            #                 # Обрезаем лишние посты
            #                 parse_res = parse_res[:cut_pos]
            #             if task.criterion.post_end_date != 0:
            #                 cut_pos = len(parse_res)
            #                 for i, el in enumerate(parse_res, start=0):
            #                     if task.criterion.post_end_date < el.dt:
            #                         cut_pos = i
            #                         end_parse = True
            #                         break
            #                 # Обрезаем лишние посты
            #                 parse_res = parse_res[cut_pos:]
            #             # max_post_id = parse_res[0].post_id
            #             # tmp_post = Post.get_post(post_id=max_post_id, task_id=task, source_id=task.target_id)
            #             # if tmp_post != None:
            #             #     end_parse = True
            #         except Exception as ex:
            #             continue
            #     # Анализ
            #     state = 'анализ'
            #     anl_params = AnalyzerParams(task_id=task.get_id(), target_id=task.target_id, min_text_len=min_text_len, max_text_len=max_text_len,
            #                             key_words=task.criterion.key_words, hashtags=task.criterion.hashtags, clear_words=task.criterion.clear_words, replace_words=task.criterion.replace_words,
            #                             forbidden_words=task.criterion.forbidden_words, post_start_date=task.criterion.post_start_date, post_end_date=task.criterion.post_end_date,
            #                             last_post_id=last_post_id, video_platform=task.criterion.video_platform, del_hashtags=task.criterion.del_hashtags,
            #                             url_action=task.criterion.url_action, min_rate=task.criterion.min_rate)
            #     proc_posts = await analyze_posts(parse_res, anl_params)
            #     # if len(proc_posts) == 0:
            #     #     reas = f'В анализируемом пуле из {post_num} постов при выполнении задачи "{task.name}" (key: {task.get_id()}) не найдено ни одного подходящего под критерии поста. Задача остановлена.'
            #     #     print(reas)
            #     #     parsers_loger.warning(reas)
            #     #     break # Если ничего подходящего в 100 записях нет, дальше можно не искать
            #     state = 'сохранение'
            #     if not last_post_id_saved and proc_posts != []:
            #         try:
            #             task.last_post_id = proc_posts[0].post_id
            #             task.save()
            #             last_post_id_saved = True
            #         except:
            #             pass
            #     await save_posts(proc_posts, task.target_id, task=task, program=task.program)
            #     #
            #     got_post_num = got_post_num + len(proc_posts)
            #     posts_got=posts_got+post_num
                #
            if parsing_mode != ParseModes.UPDATE_PERIOD.value:
                #print(f'Выполнение задачи "{task.name}" завершено. Загружено {got_post_num} постов.')
                if debug: parsers_loger.info(f'Выполнение задачи <{task.name}> завершено. Загружено {got_post_num} постов.')
                # Сохраняем состояние
                await task.refresh_task_state(ParseTaskStates.Ended.value)
                break
            # Обновляем данные задачи
            task = ParseTask.get_by_id(task.get_id())
            # Сохраняем состояние
            await task.refresh_task_state(ParseTaskStates.Sleep.value)
            if debug: parsers_loger.info(f'Задача <{task.name}> уходит в сон на {period/60/60} часов.')
            await asyncio.sleep(period)
    except Exception as ex:
        await task.refresh_task_state(ParseTaskStates.Error.value, ex)
        err_str = f'При выполнении задачи {task.name} (key: {task.get_id()}), произошла ошибка: {ex}. Задача остановлена.'
        parsers_loger.error(err_str)


