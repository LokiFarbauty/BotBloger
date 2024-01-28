'''В этом диалоге должно определятся зарегистрирован ли пользователь, либо нужно пройти процедуру регистрации'''
from operator import itemgetter
from typing import Any
from aiogram.types import CallbackQuery, ContentType, Message, FSInputFile
from aiogram_dialog import (
    Dialog, DialogManager, Window, ChatEvent, StartMode
)
from aiogram import Bot, Dispatcher, F, Router
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import SwitchTo, Start, Next, ScrollingGroup, Button, Select, Url, Cancel, Row
from aiogram_dialog.widgets.text import Const, Format
# routers
from routers.logers import bots_loger
from routers.parsing.parsers_dispatсher import parsers_dispatcher
from routers.publicate.publicators import stop_publicator_process
import routers.bots.telegram.bots as bots_unit
# views
import views.telegram.vk_sync.lexicon as lexicon
# models
from models.data.parser import Parser
from models.data.user import User
from models.data.user_bot import User_Bot
from models.data.bot import Bot as BotModel
from models.data.parse_task import ParseTask, ParseTaskStates, ParseTaskActive
from models.data.publicator import Publicator, PublicatorStates, PublicatorModes
from models.data.channel import Channel, ChannelTypes
from models.data.criterion import Criterion
# other
from datetime import datetime
# dialogs
from views.telegram.vk_sync_ads import states


async def getter_ads(**_kwargs):
    dm = _kwargs['dialog_manager']
    event_from_user = _kwargs['event_from_user']
    user_id = event_from_user.id
    greeting = 'Данный бот используется для синхронизации. ' \
               'Если Вам необходим авторепостинг из <b>ВКонтакте</b> в <b>Телеграм</b> можете воспользоваться <a href="https://t.me/VK_sync_tg_bot">синхроботом 🤖</a>. Чтобы следить за новостями развития ботов подписывайтесь на <a href="https://t.me/+YiLI2dpPsgo4OGZi">наш канал</a>.'
    return {
        "greeting": greeting,
    }



dialog_interface = (
    Window(
        Format('{greeting}'),
        getter=getter_ads,
        state=states.SG_VKSync_ADS.start,
    ),
    )

dialog_start_vk_sync_ads = Dialog(*dialog_interface)