'''Команды для терминала, он заберает их отсюда'''

# models
from models.data.bot import Bot
from models.data.user import User
from models.data.parser import Parser
from models.data_model import get_elements

# routers
from routers.console.terminal_interface import Command
from routers.dispatcher import parsing_dispatcher



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
                return f'Пользователь {user_id} не найден'
        else:
            user = await get_test_user()
        element = Bot.make(user=user, token=test_token, parse_mode='HTML', name='', url='', active=1, public=1, tg_id=0)
        element.save()
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
    parsers = Parser.select().where(Parser.name == 'service_parser' and Parser.platform == 'ВКонтакте')
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
