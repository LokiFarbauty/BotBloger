from aiogram.types import ContentType, Message
from aiogram_dialog import (
    Dialog, DialogManager, Window,
)
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import SwitchTo, Start, Next, Back
from aiogram_dialog.widgets.text import Const, Format
from aiogram.fsm.state import State, StatesGroup
# routers
from routers.logers import bots_loger
# views
# from views.telegram.tmp.lexicon import *
# from views.telegram.tmp.states import SG_enter_token_menu
# import views.telegram.tmp.states as states
# models
from models.data.parser import Parser
from models.data.user import User
# other
from datetime import datetime

class Dialog_state(StatesGroup):
    start = State()
    contacts = State()


async def getter_start(**_kwargs):
    pass
    return {
        "greeting": 'Добрый день. Этот бот подключен к системе администрирования телеграм-каналов "Бот-блогер".',
    }

async def getter_contacts(**_kwargs):
    pass
    return {
        "greeting": 'Для связи с администратором напишите сюда @loki_admin_bot.',
    }

dialog_interface = (Window(
        Format('{greeting}'),
        #Back(Const(BUTTONS['назад']), id="btn_why_token_back"),
        #SwitchTo(Const(BUTTONS['назад']), id="btn_back", state=SG_enter_token_menu.start),
        Next(Const('💬 Связь с администратором'), id="btn_to_contacts"),
        getter=getter_start,
        state=Dialog_state.start,
    ),
    Window(
        Format('{greeting}'),
        Back(Const('Назад'), id="btn_admin_contact"),
        #SwitchTo(Const(BUTTONS['назад']), id="btn_back", state=SG_enter_token_menu.start),
        getter=getter_contacts,
        state=Dialog_state.contacts,
    ),)

dialog_start = Dialog(*dialog_interface)