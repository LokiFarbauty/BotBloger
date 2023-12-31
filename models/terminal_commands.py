'''Команды для терминала, он заберает их отсюда'''
# py
from datetime import datetime

# models
from models.data.bot import Bot
from models.data.user import User
from models.data.parser import Parser
from models.data.parse_program import ParseProgram
from models.data.parse_task import ParseTask, ParseTaskStates, ParseTaskActive
from models.data_model import get_elements
from models import dm_config
from models.data.post import Post
from models.data.photo import Photo
from models.data.audio import Audio
from models.data.audio_upload import AudioUpload
from models.data.video import Video
from models.data.docs import Doc
from models.data.poll import Poll
from models.data.link import Link
from models.data.post_text_FTS import PostText
from models.data.post_hashtag import Post_Hashtag



# routers
from routers.console.terminal_interface import Command
from routers.parsing.dispatcher import parsing_dispatcher, INFINITE
import routers.bots.telegram.bots as bots_unit
from routers.logers import app_loger
from routers.bots.telegram import bots

# views
from views.telegram.dialogs_dispatcher import bot_dialogs

commands = []

# commands.append(
#      Command(name='get_users', func=User.get_users_obj, args_num=1, help='Получить пользователей из базы данных. Параметры: 1 - user_id либо username.')
# )

async def get_test_user():
    user = User.select().where(User.tg_user_id == 0)
    try:
        element = user[0]
        return element
    except Exception as ex:
        element = User.create(tg_user_id=0, username='Tester', firstname='', lastname='', first_visit=0, last_visit=0,
                           balance=0)
        element.save()
        return element

commands.append(
     Command(name='get_test_user', func=get_test_user, args_num=0, help='Создать тестового пользователя в базе данных. Параметров нет.')
)

async def create_test_bot(user_id: int = 0):
    test_token = '5724303247:AAFPORrZd8ud2u0s1nQvdtn0fOPBOieFdS8'
    mbots = get_elements(Bot, Bot.token == test_token)
    try:
        element = mbots[0]
        return element
    except Exception as ex:
        if user_id != 0:
            user = User.get_user(user_tg_id = user_id)
            if user==None:
                app_loger.warning(f'При создании тестового бота не найден пользователь.')
                return f'Пользователь {user_id} не найден'
        else:
            user = await get_test_user()
        element = Bot.make(user=user, token=test_token, parse_mode='HTML', name='', url='', active=1, public=1, tg_id=0, db_file=dm_config.DB_FILE_PATH)
        element.save()
        # Запускаем бот
        try:
            bot = bots.BotExt(test_token, 'HTML', 1, 1, *bot_dialogs)
            bots_unit.current_bots.append(bot)
            try:
                bot_info = await bot.get_me()
                # обновляем информацию о боте
                element.refresh_bot_info(bot_info.first_name, bot_info.username, bot_info.id)
                bot.name = bot_info.first_name
                bot.url = bot_info.username
                bot.tg_id = bot_info.id
            except Exception as ex:
                app_loger.warning(f'Установить связь с ботом {element.name} не удалось. Ошибка: {ex}')
            try:
                await bot.start_polling_task()
            except Exception as ex:
                app_loger.warning(f'Запустить бот {element.name} не удалось. Ошибка: {ex}')
        except Exception as ex:
            app_loger.error(f'Ошибка create_test_bot: {ex}')
        return element

commands.append(
     Command(name='create_test_bot', func=create_test_bot, args_num=0, help='Создать тестового бота. Параметры (необязательно): 1  - user_id - хозяина бота')
)

async def create_admin():
    adm_vk_token = 'vk1.a.91iecxcqhaZpqlRZ5aSZPvTJa9LmJbYPNCUkefQgipRIBZBmNoFVFOCNndqcrfchsa1a0Cj0mo0pQVMyW5Gt-nEoxnvvgBaVnbh3Z7du_enxoTlC0zPKmvpw0D1tOHzA9oTwwp3KG0jElf5VV6DL78NEmCafwO-ZzwuXEg3C4TAd8PM3A1dPZ2uNFfnHkOk-synIYGhT52OhG-exMjjXxQ'
    # Создаем пользователя
    users = User.select().where(User.tg_user_id == 0)
    try:
        user = users[0]
    except Exception as ex:
        user = User.create(tg_user_id=0, username='superadmin', firstname='', lastname='', first_visit=0, last_visit=0,
                              permissions='super', balance=100000000)
        user.save()
    # Создаем парсер
    parsers = Parser.select().where(Parser.name == 'service_parser', Parser.platform == 'ВКонтакте')
    try:
        parser = parsers[0]
    except Exception as ex:
        parser_obj = parsing_dispatcher.get_parser('ВКонтакте')
        parser = Parser.create(name='service_parser', platform=parser_obj.name, user=user, img='', file=parser_obj.file,
                                description=parser_obj.description, token=adm_vk_token, public=0)
        parser.save()
    return 'суперадмин создан'

commands.append(
     Command(name='create_admin', func=create_admin, args_num=0, help='Создать супер администратора - супер пользователя, админский парсер в ВК. Параметров нет')
)

async def get_program(name: str=''):
    # Получаем программу по имени, если не указано возвращаются все программы
    desc = ''
    if name != '':
        programs = ParseProgram.select().where(ParseProgram.name==name).order_by(ParseProgram.user.asc())
    else:
        programs = ParseProgram.select().order_by(ParseProgram.user.asc())
    for program in programs:
        # Получаем пользователя
        #user = User.get_user(user_key=program.user)
        # Фомируем расписание
        dt = datetime.fromtimestamp(program.cr_dt).strftime('%d.%m.%Y')
        desc = f'{desc}"{program.name}" (key: {program.get_id()}). Создана: {dt} {program.user.username} (key: {program.user.get_id()}, tg_id: {program.user.tg_user_id})\n'
    return desc

commands.append(
     Command(name='get_program', func=get_program, args_num=0, help="Получить программу по имени, если не указано возвращаются все. "
                                                                    "Параметры: name: str=''")
)

async def create_program(name: str, user_id: int = 0, description = ''):
    # Проверяем есть ли уже программа с таким именем у такого пользователя
    user = User.get_user(user_tg_id=user_id)
    if user == None:
        app_loger.warning(f'Пользователь с tg_id: {user_id} не найден.')
        return f'Пользователь с tg_id: {user_id} не найден.'
    programs = ParseProgram.select().where(ParseProgram.user==user | ParseProgram.name==name)
    try:
        program = programs[0]
        return f'Программа с именем "{name}" пользователем {user_id} уже создана.'
    except:
        try:
            dt = datetime.now()
            cr_dt = dt.replace(microsecond=0).timestamp()
            program = ParseProgram.create(name=name, user=user, cr_dt=cr_dt, img='', description=description)
            return f'Программа "{name}" создана.'
        except Exception as ex:
            return f'Ошибка создания программы {ex}.'

commands.append(
     Command(name='create_program', func=create_program, args_num=1, help="Создать программу парсинга. Параметры: name: str, user_id: int = 0, description = ''")
)

async def get_task(name: str=''):
    # Указываем сервисного пользователя
    user = 1
    # Получаем задачу по имени, если не указано возвращаются все задачи
    desc = ''
    if name != '':
        tasks = ParseTask.select().where(ParseTask.name==name)
    else:
        tasks = ParseTask.select().order_by(ParseTask.program.desc())
    for task in tasks:
        # Фомируем расписание
        dt = datetime.fromtimestamp(task.cr_dt).strftime('%d.%m.%Y')
        try:
            program_name = task.program.name
        except:
            program_name = 'нет'
        desc = f'{desc}"{task.name}" (key: {task.get_id()}). Программа: "{program_name}". Цель: "{task.target_name}" (id: {task.target_id}). Создана: {dt} {task.user.username} (key: {task.user.get_id()}, tg_id: {task.user.tg_user_id})\n'
    return desc

commands.append(
     Command(name='get_task', func=get_task, args_num=0, help="Получить информацию о задаче по имени, если не указано возвращаются все задачи."
                                                              " Параметры: name: str=''")
)

async def get_program_task(program_key: int):
    # Получаем задачу по имени, если не указано возвращаются все задачи
    desc = ''
    tasks = ParseTask.select().where(ParseTask.program==program_key).order_by(ParseTask.program.desc())
    for task in tasks:
        # Фомируем расписание
        dt = datetime.fromtimestamp(task.cr_dt).strftime('%d.%m.%Y')
        try:
            program_name = task.program.name
        except:
            program_name = 'нет'
        desc = f'{desc}"{task.name}" (key: {task.get_id()}). Программа: "{program_name}". Цель: "{task.target_name}" (id: {task.target_id}). Создана: {dt} {task.user.username} (key: {task.user.get_id()}, tg_id: {task.user.tg_user_id})\n'
    return desc

commands.append(
     Command(name='get_program_task', func=get_program_task, args_num=1, help="Получить информацию о задачах, входящих в программу."
                                                              " program_key: int")
)

async def get_task_params(task_key: int):
    desc = ''
    task = ParseTask.get_task(key=task_key)
    if task != None:
        # Формируем расписание
        try:
            start_date = datetime.fromtimestamp(task.post_start_date).strftime("%d.%m.%Y")
        except:
            start_date = 'не задана'
        try:
            end_date = datetime.fromtimestamp(task.post_end_date).strftime("%d.%m.%Y")
        except:
            end_date = 'не задана'
        desc = f'{desc}"{task.name}" (key: {task.get_id()}). ' \
               f'Фильтр: {task.filter}. Количество постов: {task.post_num}. Начальная дата: {start_date} ' \
               f'Конечная дата: {end_date} ' \
               f'\nКлючевые слова: {task.key_words}.\nЗапрещенные слова: {task.forbidden_words}.\n' \
               f'Удалять слова: {task.clear_words}.\nХэштеги: {task.hashtags}.\n' \
               f'Период запуска: {task.period} сек.\nМаксимальная длинная текста: {task.post_max_text_length}.\n' \
               f'Минимальная длинная текста: {task.post_min_text_length}.'
        return desc
    else:
        return f'Задача с ключом {task_key} не найдена.'

commands.append(
     Command(name='get_task_params', func=get_task_params, args_num=1, help="Получить параметры задачи."
                                                              " Параметры: task_key: int")
)

async def get_task_status(task_key: int):
    desc = ''
    task = ParseTask.get_task(key=task_key)
    if task != None:
        # Формируем расписание
        active = ParseTaskActive(value=task.active)
        state = ParseTaskStates(value=task.state)
        desc = f'{desc}"{task.name}" (key: {task.get_id()}). ' \
               f'Состояние: {state.name}. Активность: {active.name}. Последний выгруженный пост: {task.last_post_id}. Ошибка: {task.error}'
        return desc
    else:
        return f'Задача с ключом {task_key} не найдена.'

commands.append(
     Command(name='get_task_status', func=get_task_status, args_num=1, help="Получить состояние задачи."
                                                              " Параметры: task_key: int")
)

async def create_task_parse_arhive(name: str, target_name: str, program_key: int=0,  filter='all'):
    # Указываем сервисного пользователя
    user = 1
    # Проверяем есть ли программа с таким ключем
    # пример create_task_parse_arhive: Моя страница, ogpu_nkvd, 1
    if program_key>0:
        program = ParseProgram.get_program(key=program_key)
        if program == None:
            return f'Программа: {program_key} не найдена.'
    else:
        program = None
    # Проверяем есть ли такой ресурс в ВК
    s_parse_mld = Parser.get_service_parser()
    parser = parsing_dispatcher.get_parser('ВКонтакте')
    if parser != None and s_parse_mld != None:
        try:
            target_id, target_type = await parser.get_vk_object_id(target_name, s_parse_mld.token, with_type=True)
            if type(target_id) is str or target_id == None:
                return f'Ошибка: {target_id}'
            # if target_type == 'user':
            #     res = await parser.get_vk_user_info(target_id, s_parse_mld.token)
            # elif target_type == 'group':
            #     res = await parser.get_vk_user_info(target_id, s_parse_mld.token)
            # else:
            #     return f'Неизвестный тип объекта: {program_key}'
            # Создаем задачу
            dt = datetime.now()
            cr_dt = dt.replace(microsecond=0).timestamp()
            task = ParseTask.create(name=name, user=user, program=program, parser=s_parse_mld, target_id=target_id,
                                    target_name=target_name, target_type=target_type, filter=filter,
                                    cr_dt=cr_dt, post_num=INFINITE, state=ParseTaskStates.Good.value, last_post_id=0,
                                    active=ParseTaskActive.Stopped.value)
            return f'Задача "{name}" создана.'
        except Exception as ex:
            return f'Ошибка: {ex}'
    else:
        return 'Парсер не найден.'

commands.append(
     Command(name='create_task_parse_arhive', func=create_task_parse_arhive, args_num=2, help="Создать задачу для парсинга архива (парсит стену целиком). "
                                                                                 "Параметры: name: str, target_name: str, program_key: int=0,  filter='all'")
)

async def clear_posts_in_db():
    num = 0
    try:
        posts = Post.select()
        for post in posts:
            num+=1
            # Удаляем картинки
            photos = Photo.delete().where(Photo.owner == post)
            photos.execute()
            # Удаляем аудио
            audios = Audio.select().where(Audio.owner == post)
            for audio in audios:
                audio_uploads = AudioUpload.select().where(AudioUpload.audio == audio)
                for audio_upload in audio_uploads:
                    audio_upload.delete_instance()
                audio.delete_instance()
            # Удаляем видео
            videos = Video.delete().where(Video.owner == post)
            videos.execute()
            # Удаляем линки
            links = Link.delete().where(Link.owner == post)
            links.execute()
            # Удаляем доки
            docs = Doc.delete().where(Doc.owner == post)
            docs.execute()
            # Удаляем опросы
            polls = Poll.delete().where(Poll.owner == post)
            polls.execute()
            # Удаляем хэштэги
            hashtags = Post_Hashtag.delete().where(Post_Hashtag.post == post)
            hashtags.execute()
            # Удаляем пост и текст
            PostText.delete_by_id(post.get_id())
            post.delete_instance()
    except Exception as ex:
        print(ex)
        return f'Удалено {num} постов.'
    return f'Удалено {num} постов.'

commands.append(
     Command(name='clear_posts_in_db', func=clear_posts_in_db, args_num=0, help="Удалить все посты из базы."
                                                              " Параметры: нет")
)