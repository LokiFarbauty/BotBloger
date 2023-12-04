from aiogram.types import CallbackQuery, ContentType, Message, FSInputFile, ReplyKeyboardRemove
from aiogram import Bot, Dispatcher, F, Router
from aiogram_dialog import (
    ChatEvent, Dialog, DialogManager, setup_dialogs,
    ShowMode, StartMode, Window,
)
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Cancel, Button, Row, Select, SwitchTo, Start, Url
from aiogram_dialog.widgets.text import Const, Format, Multi, ScrollingText
from routers.bots.lexicon import *
from routers.parsing.interface_parser import ParseParams
from routers.dispatcher import parsing_dispatcher
from routers.bots.loger import bots_loger
import routers.bots.telegram.states as states


async def start_main_menu(**_kwargs):
    #dm = _kwargs['dialog_manager']
    #args[1].dialog_data = data
    pass

async def getter_start_menu(**_kwargs):
    try:
        dm = _kwargs['dialog_manager']
        event_from_user = _kwargs['event_from_user']
        user_id = event_from_user.id
    except Exception as ex:
        user_id = 0
        bots_loger.error(f'Ошибка getter_start_menu: {ex}')
    return {
        "greeting": GREETINGS['старт'],
        "user_id": user_id,
        }


dialog_start_menu = Dialog(
    Window(
        Format('{greeting}'),
        Url(Const(BUTTONS['авторизация']), url=Format('https://api.vk.com/oauth/authorize?client_id=51753414&redirect_uri=https://tops-actively-lion.ngrok-free.app/vkCallback&scope=wall,groups,video,photos,offline&response_type=code&state={user_id}'), id="btn_auth",),
        # Row(
        #     Start(Const(BUTTONS['новое']), id="dlg_news", state=states.SG_news.start),
        #     Start(Const(BUTTONS['найти']), id="dlg_find", state=states.SG_find_post.input_words),
        # ),
        # Row(
        #     Start(Const(START_BUTTONS['топ']), id="dlg_top", state=states.SG_tops.start),
        #     Start(Const(START_BUTTONS['случайно']), id="dlg_random", state=states.SG_random.start),
        # ),
        # Row(
        #     Start(Const(START_BUTTONS['избранное']), id="dlg_favour", state=states.SG_favourites.start),
        #     Start(Const(START_BUTTONS['предложить']), id="dlg_offer", state=states.SG_offer_post.add_text),
        # ),
        state=states.SG_start_menu.start,
    ),
    getter=getter_start_menu,
)