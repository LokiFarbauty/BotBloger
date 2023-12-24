from aiogram.types import CallbackQuery, ContentType, Message, FSInputFile, ReplyKeyboardRemove
from aiogram import Bot, Dispatcher, F, Router
from aiogram_dialog import (
    ChatEvent, Dialog, DialogManager, setup_dialogs,
    ShowMode, StartMode, Window,
)
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Cancel, Button, Row, Select, SwitchTo, Start, Next, Back
from aiogram_dialog.widgets.text import Const, Format, Multi, ScrollingText
from routers.bots.lexicon import *
from routers.parsing.interface_parser import ParseParams
from routers.dispatcher import parsing_dispatcher
from routers.bots.loger import bots_loger
from routers.bots.telegram.states import SG_enter_token_menu
from routers.bots.telegram import states
#
from models.data.parser import Parser
from models.data.user import User
from datetime import datetime
import routers.bots.telegram.states as states


async def get_user_id(user_name, token):
    user_id = 0 # 0 - не правильный токен
    parser = parsing_dispatcher.get_parser('ВКонтакте')
    if parser != None:
        user_id = await parser.get_vk_object_id(user_name, token)
    else:
        user_id = -1 # ошибка парсера
    return user_id

async def get_parser(user_id, access_token, vk_user_id):
    now_dt = datetime.now().replace(microsecond=0)
    now_dt = now_dt.timestamp()
    user = User.get_user(user_tg_id=user_id)
    parser = Parser.get_parser(user=user, token=access_token, platform_user_id=vk_user_id)
    if parser == None:
        parser = Parser.create(name=f'VKParser_{vk_user_id}', platform='ВКонтакте', platform_user_id=vk_user_id,
                               user=user, token=access_token, public=0, cr_dt=int(now_dt))
        parser.save()
    return parser

async def start_main_menu(**_kwargs):
    #dm = _kwargs['dialog_manager']
    #args[1].dialog_data = data
    pass

async def getter_start_menu(**_kwargs):
    dm = _kwargs['dialog_manager']
    bot = _kwargs['bot']
    event_chat = _kwargs['event_chat']
    try:
        user = dm.start_data['user']
        user_name = f'{user.firstname} {user.lastname}'
        # Проверяем создан ли для пользователя парсер
        user = User.get_user(user_key=user.id)
        parser = Parser.get_parser(user=user)
        if parser != None:
            # Парсер уже создан выводим меню управления.
            # await bot.send_message(event_chat.id, parser.name)
            await dm.start(states.SG_bot_config.show_menu, mode=StartMode.RESET_STACK, data={'user': user})
            return
    except:
        user_name = ''
    return {
        "greeting": GREETINGS['старт'].format(user_name),
        }

async def token_handler(message: Message, message_input: MessageInput,
                       dialog_manager: DialogManager):
    try:
        # Вычленяем нужную информацию из ссылки
        ac_url=message.text
        # получаем токен
        t_pos = ac_url.find('access_token=')
        if t_pos == -1:
            if ac_url.find('vk1.') != -1:
                access_token = ac_url
            else:
                await message.answer(GREETINGS['нет токена'])
                return
        else:
            end_t_pos = ac_url.find('&', t_pos)
            access_token = ac_url[t_pos+len('access_token='):end_t_pos]
        dialog_manager.dialog_data['access_token'] = access_token
        # получаем пользователя
        t_pos = ac_url.find('user_id=')
        if t_pos == -1:
            #await message.answer(GREETINGS['нет токена'])
            await dialog_manager.start(state=SG_enter_token_menu.get_user_id, data=dialog_manager.dialog_data)
            return
        end_t_pos = ac_url.find('&', t_pos)
        vk_user_id = ac_url[t_pos + len('user_id='):end_t_pos]
        dialog_manager.dialog_data['vk_user_id'] = vk_user_id
        # Формируем парсер
        parser = await get_parser(message.from_user.id, access_token, vk_user_id)
        await message.answer(f'Парсер: {parser.name}')
    except Exception as ex:
        bots_loger.error(f'Ошибка words_handler: {ex}')
        await message.answer(GREETINGS['ошибка'])
        pass

    #await dialog_manager.start(states.SG_find_post.show_result, mode=StartMode.RESET_STACK, data={'cases': cases})
    # Завершаем диалог
    #await dialog_manager.done()

async def user_id_handler(message: Message, message_input: MessageInput,
                       dialog_manager: DialogManager):
    word = message.text
    pos = word.find('https://vk.com/')
    if pos != -1:
        user_name = word[pos+len('https://vk.com/'):]
    else:
        user_name = word
    try:
        access_token = dialog_manager.start_data['access_token']
        # Получаем user_id
        user_id = await get_user_id(user_name, access_token)
        if user_id == -1: # Ошибка получения парсера
            await message.answer(GREETINGS['ошибка'])
            return
        if type(user_id) is str: # Не правильный токен
            await message.answer(f'Ошибка: {str(user_id)}')
            await dialog_manager.back()
        elif user_id == 0:
            await message.answer('Ошибка: введен не верный токен.')
            await dialog_manager.back()
        else:
            parser = await get_parser(message.from_user.id, access_token, user_id)
            await message.answer(f'Парсер: {parser.name}')
    except Exception as ex:
        await message.answer(GREETINGS['ошибка'])
        return


async def getter_where_token(**_kwargs):
    return {
        "greeting": GREETINGS['как получить токен'],
    }
async def getter_why_token(**_kwargs):
    return {
        "greeting": GREETINGS['зачем токен'],
    }

async def getter_token_got(**_kwargs):
    return {
        "greeting": GREETINGS['у меня есть токен'],
    }

async def getter_user_id(**_kwargs):
    return {
        "greeting": GREETINGS['у меня есть юзер ид'],
    }



dialog_start_menu = Dialog(
    Window(
        Format('{greeting}'),
        MessageInput(token_handler, content_types=[ContentType.TEXT]),
        Start(Const(BUTTONS['зачем токен']), id="btn_why_token", state=states.SG_enter_token_menu.why_token),
        Start(Const(BUTTONS['как получить токен']), id="btn_where_token", state=states.SG_enter_token_menu.where_token),
        Start(Const(BUTTONS['у меня есть токен']), id="btn_token_got", state=states.SG_enter_token_menu.token_got),
        state=SG_enter_token_menu.start,
    ),
    Window(
        Format('{greeting}'),
        #Back(Const(BUTTONS['назад']), id="btn_why_token_back"),
        SwitchTo(Const(BUTTONS['назад']), id="btn_back", state=SG_enter_token_menu.start),
        getter=getter_why_token,
        state=SG_enter_token_menu.why_token,
    ),
    Window(
        Format('{greeting}'),
        #Back(Const(BUTTONS['назад']), id="btn_where_token_back"),
        SwitchTo(Const(BUTTONS['назад']), id="btn_back", state=SG_enter_token_menu.start),
        getter=getter_where_token,
        state=SG_enter_token_menu.where_token,
    ),
    Window(
        Format('{greeting}'),
        MessageInput(token_handler, content_types=[ContentType.TEXT]),
        #Back(Const(BUTTONS['назад']), id="btn_getter_token_got_back"),
        SwitchTo(Const(BUTTONS['назад']), id="btn_back", state=SG_enter_token_menu.start),
        getter=getter_token_got,
        state=SG_enter_token_menu.token_got,
    ),
    Window(
        Format('{greeting}'),
        MessageInput(user_id_handler, content_types=[ContentType.TEXT]),
        #Back(Const(BUTTONS['назад']), id="btn_get_user_id_back"),
        SwitchTo(Const(BUTTONS['назад']), id="btn_back", state=SG_enter_token_menu.start),
        getter=getter_user_id,
        state=SG_enter_token_menu.get_user_id,
    ),
    getter=getter_start_menu,
)