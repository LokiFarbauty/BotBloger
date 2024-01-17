'''Команды для терминала, он заберает их отсюда'''
# py
from datetime import datetime

# models
from models.data.bot import Bot, BotStates
from models.data.user import User
from models.data.parser import Parser
from models.data.parse_program import ParseProgram
from models.data.parse_task import ParseTask, ParseTaskStates, ParseTaskActive
from models.data.criterion import Criterion
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
from models.data.publicator import Publicator, PublicatorStates, PublicatorModes
from models.data.channel import Channel, ChannelTypes


# routers
from routers.console.terminal_interface import Command
from routers.parsing.dispatcher import parsing_dispatcher, INFINITE
from routers.logers import app_loger
from routers.bots.telegram import bots
import routers.bots.telegram.bots as bots_unit

# views
#from views.telegram.tmp.dialogs_dispatcher import bot_dialogs
from views.telegram.none_interface.dialogs_dispatcher import BotView

commands = []

# commands.append(
#      Command(name='get_users', func=User.get_users_obj, args_num=1, help='Получить пользователей из базы данных. Параметры: 1 - user_id либо username.')
# )


async def get_users():
    try:
        user_desc = ''
        users = User.select()
        for user in users:
            user_desc = f'{user_desc}"{user.username}", key: {user.get_id()}, tg_id: {user.tg_user_id}, first_name: "{user.firstname}", last_name: "{user.lastname}"\n'
        if user_desc != '':
            return user_desc
        else:
            return 'Пользователей нет.'
    except Exception as ex:
        return f'Ошибка: {ex}'

commands.append(
     Command(name='get_users', func=get_users, args_num=0, help="Вывести список пользователей."
                                                              " Параметры: нет.")
)

async def get_user(tg_id: int):
    try:
        user = User.get_user(user_tg_id=tg_id)
        if user != None:
            return f'Key: {user.get_id()}'
        else:
            return f'Пользователь не найден'
    except Exception as ex:
        return f'Ошибка: {ex}'

commands.append(
     Command(name='get_user', func=get_user, args_num=1, help="Получить ключ пользователя по tg_id."
                                                              " Параметры: tg_id: int")
)

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
            bot_dialogs = BotView.dialogs
            bot = bots.BotExt(test_token, 'HTML', 1, 1, *bot_dialogs)
            bots_unit.current_bots.append(bot)
            try:
                bot_info = await bot.get_me()
                # обновляем информацию о боте
                element.refresh_bot_info(name=bot_info.first_name, url=bot_info.username, tg_id=bot_info.id, state=BotStates.InWork.value)
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

async def create_bot(user_tg_id: int, token: str, active=True):
    mbots = get_elements(Bot, Bot.token == token)
    try:
        element = mbots[0]
        return 'Бот с указанным токеном уже создан.'
    except Exception as ex:
        if user_tg_id != 0:
            user = User.get_user(user_tg_id = user_tg_id)
            if user==None:
                app_loger.warning(f'При создании бота не найден пользователь с id {user_tg_id}.')
                return f'При создании бота не найден пользователь с id {user_tg_id}.'
        else:
            user = await get_test_user()
        element = Bot.make(user=user, token=token, parse_mode='HTML', name='', url='', active=1, public=1, tg_id=0, db_file=dm_config.DB_FILE_PATH)
        element.save()
        # Запускаем бот
        try:
            bot_dialogs = BotView.dialogs
            bot = bots.BotExt(token, 'HTML', 1, 1, *bot_dialogs)
            bots_unit.current_bots.append(bot)
            try:
                bot_info = await bot.get_me()
                # обновляем информацию о боте
                element.refresh_bot_info(bot_info.first_name, bot_info.username, bot_info.id, state=BotStates.InWork.value)
                bot.name = bot_info.first_name
                bot.url = bot_info.username
                bot.tg_id = bot_info.id
            except Exception as ex:
                app_loger.warning(f'Установить связь с ботом {element.name} не удалось. Ошибка: {ex}')
            try:
                await bot.start_polling_task()
            except Exception as ex:
                app_loger.warning(f'Запустить бот {element.name} не удалось. Ошибка: {ex}')
                try:
                    element.refresh_bot_info(bot_info.first_name, bot_info.username, bot_info.id,
                                        state=BotStates.InWork.value)
                except:
                    pass
        except Exception as ex:
            app_loger.error(f'Ошибка create_bot: {ex}')
        return element

commands.append(
     Command(name='create_bot', func=create_bot, args_num=0, help='Создать бота. Параметры: user_tg_id: int, token: str, active=True')
)

async def get_bots():
    # Указываем сервисного пользователя
    user = 1
    desc = ''
    # Получаем задачу по имени, если не указано возвращаются все задачи
    bots = Bot.select()
    for bot in bots:
        desc = f'{desc}"{bot.name}" (создатель: {bot.user.username}, адрес: {bot.url}, tg_id: {bot.tg_id}, статус: {BotStates(bot.state).name}, автозапуск: {bot.active}, токен:{bot.token}).\n'
    if desc == '':
        desc = 'Боты не найдены.'
    return desc

commands.append(
     Command(name='get_bots', func=get_bots, args_num=0, help="Получить информацию о добавленых в базу ботах."
                                                              " Параметры: нет")
)

async def delete_bot(bot_key_or_name):
    bot = None
    try:
        if type(bot_key_or_name) is int:
            bot = Bot.get_by_id(bot_key_or_name)
        if type(bot_key_or_name) is str:
            bot = Bot.get_bot(name=bot_key_or_name)
        if bot != None:
            bot.delete_instance()
        else:
            return f'Бот "{bot_key_or_name}" не найден.'
    except Exception as ex:
        print(ex)
        return f'Удалить бота "{bot_key_or_name}" не удалось. Причина: {ex}'
    return f'Бот "{bot_key_or_name}" удален.'

commands.append(
     Command(name='delete_bot', func=delete_bot, args_num=1, help="Удалить бот из базы."
                                                              " Параметры: 1 - имя либо ключ бота.")
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
            start_date = datetime.fromtimestamp(task.criterion.post_start_date).strftime("%d.%m.%Y")
        except:
            start_date = 'не задана'
        try:
            end_date = datetime.fromtimestamp(task.criterion.post_end_date).strftime("%d.%m.%Y")
        except:
            end_date = 'не задана'
        desc = f'{desc}"{task.name}" (key: {task.get_id()}). ' \
               f'Фильтр: {task.filter}. Количество постов: {task.post_num}. Начальная дата: {start_date} ' \
               f'Конечная дата: {end_date} ' \
               f'\nКлючевые слова: {task.criterion.key_words}.\nЗапрещенные слова: {task.criterion.forbidden_words}.\n' \
               f'Удалять слова: {task.criterion.clear_words}.\nХэштеги: {task.criterion.hashtags}.\n' \
               f'Период запуска: {task.period} сек.\nМаксимальная длинная текста: {task.criterion.post_max_text_length}.\n' \
               f'Минимальная длинная текста: {task.criterion.post_min_text_length}.'
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

async def create_task(name: str, target_name: str, program_key: int=0,  filter='all'):
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
                return f'Ошибка: найти ресурс "{target_name}" не удалось.'
            # if target_type == 'user':
            #     res = await parser.get_vk_user_info(target_id, s_parse_mld.token)
            # elif target_type == 'group':
            #     res = await parser.get_vk_user_info(target_id, s_parse_mld.token)
            # else:
            #     return f'Неизвестный тип объекта: {program_key}'
            # Создаем задачу
            dt = datetime.now()
            cr_dt = dt.replace(microsecond=0).timestamp()
            criterion = Criterion.create(target_id=target_id,
                                    target_name=target_name, target_type=target_type)
            task = ParseTask.create(name=name, user=user, program=program, parser=s_parse_mld, criterion=criterion, target_id=target_id,
                                    target_name=target_name, target_type=target_type, filter=filter,
                                    cr_dt=cr_dt, post_num=INFINITE, state=ParseTaskStates.Stopped.value, last_post_id=0,
                                    active=ParseTaskActive.Stopped.value, period=0)
            return f'Задача "{name}" создана.'
        except Exception as ex:
            return f'Ошибка: {ex}'
    else:
        return 'Парсер не найден.'

commands.append(
     Command(name='create_task', func=create_task, args_num=2, help="Создать задачу для парсинга. Параметры: name: str, target_name: str, program_key: int=0,  filter='all'")
)

async def delete_task(task_key_or_name):
    try:
        if type(task_key_or_name) is int:
            task = ParseTask.get_by_id(task_key_or_name)
        if type(task_key_or_name) is str:
            task = ParseTask.get_task(name=task_key_or_name)
        if task != None:
            task.delete_instance()
        else:
            return f'Задача "{task_key_or_name}" не найдена.'
    except Exception as ex:
        print(ex)
        return f'Удалить задачу "{task_key_or_name}" не удалось. Причина: {ex}'
    return f'Задача "{task_key_or_name}" удалена.'

commands.append(
     Command(name='delete_task', func=delete_task, args_num=1, help="Удалить задачу."
                                                              " Параметры: 1 - имя либо ключ задачи.")
)

async def create_channel(tg_id: int, user_key=1, type=0):
    try:
        bot = bots_unit.current_bots[0]
        #chat = await aioBot(bot).get_chat(tg_id)
        user = User.get_by_id(user_key)
        chat = await bot.get_chat(tg_id)
        name = chat.full_name
        url = chat.username
        channel = Channel.get_channel(user=user, name=name, url=url, channel_id=tg_id)
        if channel == None:
            channel = Channel.create(user=user, name=name, url=url, channel_tg_id=tg_id, type=type)
            return f'Канал "{name}" (key: {channel.get_id()}, tg_id: {tg_id}) для пользователя {user.username} успешно создан.'
        else:
            return f'Канал "{name}" (key: {channel.get_id()}, tg_id: {tg_id}) пользователем {user.username} уже создан.'
        pass
    except Exception as ex:
        return f'Ошибка: {ex}'

commands.append(
     Command(name='create_channel', func=create_channel, args_num=1, help="Создать канал. Параметры: tg_id: int, user_key=1, type=0")
)

async def get_channels():
    try:
        ch_desc = ''
        channels = Channel.select()
        for ch in channels:
            ch_desc = f'{ch_desc}"{ch.name}", key: {ch.get_id()}, tg_id: {ch.channel_tg_id}, user: "{ch.user.username}"(key: {ch.user.get_id()}), url: "{ch.url}", type: {ChannelTypes(ch.type).name}\n'
        if ch_desc != '':
            return ch_desc
        else:
            return 'Каналов нет.'
    except Exception as ex:
        return f'Ошибка: {ex}'

commands.append(
     Command(name='get_channels', func=get_channels, args_num=0, help="Вывести список созданных каналов."
                                                              " Параметры: нет.")
)

async def get_channel(tg_id: int, user_key: int):
    try:
        user = User.get_by_id(user_key)
        channel = Channel.get_channel(channel_id=tg_id, user=user)
        if channel != None:
            return f'Key: {channel.get_id()}'
        else:
            return f'Канал не найден'
    except Exception as ex:
        return f'Ошибка: {ex}'

commands.append(
     Command(name='get_channel', func=get_channel, args_num=2, help="Получить ключ канала по tg_id и user_key."
                                                              " Параметры: tg_id: int, user_key: int")
)

async def delete_channel(task_key_or_name, user_key = 1):
    ch = None
    try:
        if type(task_key_or_name) is int:
            ch = Channel.get_by_id(task_key_or_name)
        if type(task_key_or_name) is str:
            user = User.get_by_id(user_key)
            ch = Channel.get_channel(name=task_key_or_name, user=user)
        if ch != None:
            ch.delete_instance()
        else:
            return f'Канал "{task_key_or_name}" не найден.'
    except Exception as ex:
        print(ex)
        return f'Удалить канал "{task_key_or_name}" не удалось. Причина: {ex}'
    return f'Канал "{task_key_or_name}" удален.'

commands.append(
     Command(name='delete_channel', func=delete_channel, args_num=1, help="Удалить канал."
                                                              " Параметры: 1 - имя либо ключ канала.")
)


async def create_publicator(name: str, channel_key: int, task_key: int, bot_key: int, telegraph_token: str, user_key = 1):
    try:
        dt = datetime.now()
        cr_dt = dt.replace(microsecond=0).timestamp()
        # Указываем сервисного пользователя
        user = User.get_by_id(user_key)
        # Получаем бота
        bot_mld = Bot.get_by_id(bot_key)
        # Получаем канал
        channel = Channel.get_by_id(channel_key)
        # Получаем задачу
        task = ParseTask.get_by_id(task_key)
        # Проверяем есть ли публикатор с таким ключем
        # пример create_publicator: dump, 1, 1, 1, 56cbd6664bcc26ea2e247b50805cb2c3c12efc70bbf3d3dd5148ee1a02ad
        publicator = Publicator.get_publicator(name=name, channel=channel, user=user)
        if publicator == None:
            criterion = Criterion.create(target_id=task.target_id,
                                         target_name=task.target_name, target_type=task.target_type)
            publicator = Publicator.create(name=name, img='', channel=channel, user=user,
                                           parse_task=task_key, criterion=criterion, mode=PublicatorModes.Single.value, period=0, bot=bot_mld,
                                           telegraph_token=telegraph_token, author_caption='', author_name=bot_mld.name, cr_dt=cr_dt,
                                           author_url=f'https://t.me/{bot_mld.url}', premoderate=0, state=PublicatorStates.Stopped.value)
            return f'Публикатор {publicator.name} (key: {publicator.get_id()}) успешно создан.'
        else:
            return f'Публикатор {name} пользователем {user.username} уже создан.'
    except Exception as ex:
        return f'Ошибка: {ex}'

commands.append(
     Command(name='create_publicator', func=create_publicator, args_num=5, help="Создать публикатор."
                                                              " Параметры: name: str, channel_key: int, task_key: int, bot_key: int, telegraph_token: str, user_key = 1")
)

async def get_publicators():
    try:
        ch_desc = ''
        publicators = Publicator.select()
        for ch in publicators:
            ch_desc = f'{ch_desc}"{ch.name}" (key: {ch.get_id()}), task: "{ch.parse_task.name}", user: "{ch.user.username}",' \
                      f' mode: "{PublicatorModes(ch.mode).name}", period: "{ch.period}", bot: "{ch.bot.name}", state: "{PublicatorStates(ch.mode).name}"\n'
        if ch_desc != '':
            return ch_desc
        else:
            return 'Публикаторов нет.'
    except Exception as ex:
        return f'Ошибка: {ex}'

commands.append(
     Command(name='get_publicators', func=get_publicators, args_num=0, help="Вывести список созданных публикаторов."
                                                              " Параметры: нет.")
)


async def delete_publicator(task_key_or_name, user_key = 1):
    ch = None
    try:
        if type(task_key_or_name) is int:
            ch = Publicator.get_by_id(task_key_or_name)
        if type(task_key_or_name) is str:
            user = User.get_by_id(user_key)
            ch = Publicator.get_publicator(name=task_key_or_name, user=user)
        if ch != None:
            ch.criterion.delete_instance()
            ch.delete_instance()
        else:
            return f'Публикатор "{task_key_or_name}" не найден.'
    except Exception as ex:
        print(ex)
        return f'Удалить публикатор "{task_key_or_name}" не удалось. Причина: {ex}'
    return f'Публикатор "{task_key_or_name}" удален.'

commands.append(
     Command(name='delete_publicator', func=delete_publicator, args_num=1, help="Удалить публикатор."
                                                              " Параметры: task_key_or_name, user_key = 1")
)

async def delete_post(post_key: int):
    try:
        post = Post.get_by_id(post_key)
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
        return f'Ошибка: {ex}.'
    return f'Пост удален.'

commands.append(
     Command(name='delete_post', func=delete_post, args_num=0, help="Удалить пост из базы."
                                                              " Параметры: post_key: int")
)

async def delete_task_posts(task_key: int):
    num = 0
    try:
        posts = Post.select().where(Post.parse_task==task_key)
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
        return f'Ошибка: {ex}.'
    return f'Удалено {num} постов.'

commands.append(
     Command(name='delete_task_posts', func=delete_task_posts, args_num=0, help="Удалить все посты из базы, спарсенные по задаче."
                                                              " Параметры: task_key: int"))

async def delete_word_posts(word: str):
    num = 0
    try:
        posts = PostText.search(term=word, with_score=True, explicit_ordering=True)
        for post_text_mld in posts:
            num+=1
            # Получаем пост
            post = Post.get_by_id(post_text_mld.get_id())
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
        return f'Ошибка: {ex}.'
    return f'Удалено {num} постов.'

commands.append(
     Command(name='delete_word_posts', func=delete_word_posts, args_num=1, help="Удалить все посты из базы, содержащие конкретное слово."
                                                              " Параметры: word: str"))

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
        return f'Ошибка: {ex}.'
    return f'Удалено {num} постов.'

commands.append(
     Command(name='clear_posts_in_db', func=clear_posts_in_db, args_num=0, help="Удалить все посты из базы."
                                                              " Параметры: нет")
)