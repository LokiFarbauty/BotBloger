'''В этом диалоге должно определятся зарегистрирован ли пользователь, либо нужно пройти процедуру регистрации'''

from aiogram.types import CallbackQuery, ContentType, Message, FSInputFile
from aiogram_dialog import (
    Dialog, DialogManager, Window,
)
from aiogram import Bot, Dispatcher, F, Router
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import SwitchTo, Start, Next, Back, Button
from aiogram_dialog.widgets.text import Const, Format
from aiogram.fsm.state import State, StatesGroup
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
from views.telegram.vk_sync import states
from views.telegram.vk_sync.dialogs.dlg_config_bot import SG_bot_config






async def check_user_registration(user_tg_id: int):
    # Проверяем зарегистрирован ли пользователь (Заполнил все необходимое для синхронизации)
    user_mld = User.get_user(user_tg_id=user_tg_id)
    # Проверяем создал ли пользователь бота
    user_bot_mld = BotModel.get_bot(user=user_mld)
    if user_bot_mld == None:
        is_registered = False
    else:
        is_registered = True
    return is_registered

async def getter_start(**_kwargs):
    dm = _kwargs['dialog_manager']
    event_from_user = _kwargs['event_from_user']
    user_id = event_from_user.id
    is_registered = await check_user_registration(user_tg_id=user_id)
    is_not_registered = not is_registered
    if not is_registered:
        greeting = lexicon.GREETINGS['main_menu_grt'].format(sentence=lexicon.SENTENCE['reg_need'])
    else:
        user_mld = User.get_user(user_tg_id=user_id)
        user_bot_mld = BotModel.get_bot(user=user_mld)
        channel = Channel.get_channel(user=user_mld)
        parse_task = ParseTask.get_task(user=user_mld)
        try:
            greeting = f'С возвращением <b>{user_mld.firstname} {user_mld.lastname}</b>! У Вас уже имеется настроенная синхронизация телеграм-канала ' \
                    f'<b>"{channel.name}"</b> и ВК-страницы <b>"{parse_task.target_name}"</b> через бот <b>"{user_bot_mld.name}"</b>.'
        except Exception as ex:
            greeting = ex
    return {
        "greeting": greeting,
        "is_registered": is_registered,
        "is_not_registered": is_not_registered,
    }

async def event_cancel_sync(callback: CallbackQuery, button: Button,
                    dialog_manager: DialogManager):
    # Проверяем зарегистрирован ли пользователь (Заполнил все необходимое для синхронизации)
    user_id = callback.from_user.id
    user_mld = User.get_user(user_tg_id=user_id)
    bot = callback.bot
    # Проверяем создал ли пользователь бота
    user_bot_mld = BotModel.get_bot(user=user_mld)
    # Получаем парсер
    parser = Parser.get_parser(user=user_mld)
    #
    channel = Channel.get_channel(user=user_mld)
    #
    parse_task = ParseTask.get_task(user=user_mld)
    #
    try:
        criterion = parse_task.criterion
    except:
        criterion = None
    #
    publicator = Publicator.get_publicator(channel=channel, user=user_mld)
    #
    try:
        criterion_pub = publicator.criterion
    except:
        criterion_pub = None
    # Останавливаем бот
    bot_tg_id = user_bot_mld.tg_id
    for bot_el in bots_unit.current_bots:
        try:
            if bot_el.tg_id == int(bot_tg_id):
                was_cancelled = await bot_el.stop_polling()
                bots_loger.info(was_cancelled)
        except Exception as ex:
            bots_loger.error(f'Ошибка при остановке бота (удаление синхронизации) <{bot_tg_id}>: {ex}')
    # Останавливаем парсинг
    res = parsers_dispatcher.stop_task(parse_task.name)
    bots_loger.info(res)
    # Останавливаем публикатор
    res = stop_publicator_process(publicator.name)
    bots_loger.info(f'Публикатор <{publicator.name}> - <{res}>')
    # Удаляем все
    try:
        if publicator != None:
            publicator.delete_instance()
        if parse_task != None:
            parse_task.delete_instance()
        if criterion_pub != None:
            criterion_pub.delete_instance()
        if criterion != None:
            criterion.delete_instance()
        # Удаляем пользователей бота
        User_Bot.delete().where(User_Bot.bot == user_bot_mld).execute()
        if user_bot_mld != None:
            user_bot_mld.delete_instance()
        if parser != None:
            parser.delete_instance()
        if channel != None:
            channel.delete_instance()
        await bot.send_message(user_id, '✅ Синхронизация успешно удалена.')
        await dialog_manager.done()
    except Exception as ex:
        try:
            await callback.answer('Ошибка удаления синхронизации!')
        except:
            pass
        return




async def event_make_vk_sync(callback: CallbackQuery, button: Button,
                    dialog_manager: DialogManager):
    try:
        #await callback.answer('...')
        pass
    except Exception as ex:
        pass

dialog_interface = (Window(
        Format('{greeting}'),
        #SwitchTo(Const(lexicon.BUTTONS['reg']), id="btn_reg", state=SG_enter_token_menu.start, when=F["is_not_registered"]),
        Start(Const(lexicon.BUTTONS['reg']), id="btn_reg", state=states.SG_enter_token_menu.make_vk_sync, on_click=event_make_vk_sync, when=F["is_not_registered"]),
        #SwitchTo(Const(lexicon.BUTTONS['config']), id="btn_config", state=SG_bot_config.show_menu, when=F["is_registered"]),
        #Start(Const(lexicon.BUTTONS['config']), id="btn_config", state=SG_bot_config.show_menu, when=F["is_registered"]),
        Button(Const(lexicon.BUTTONS['cancel_sync']), id="btn_cancel_sync", on_click=event_cancel_sync, when=F["is_registered"]),
        # Start(Const(lexicon.BUTTONS['add_sub']), id="btn_add_sub", state=states.SG_enter_token_menu.make_vk_sync,
        #       on_click=event_make_vk_sync, when=F["is_registered"]),

    getter=getter_start,
        state=states.SG_VKSync.start,
        ),
    )

dialog_start_vk_sync = Dialog(*dialog_interface)