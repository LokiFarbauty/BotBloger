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
from views.telegram.vk_sync import states
from views.telegram.vk_sync.dialogs.dlg_config_bot import SG_bot_config
from views.telegram.vk_sync.interface_config import NUM_FREE_SYNC


async def getter_confirm_remove_sync(**_kwargs):
    dm = _kwargs['dialog_manager']
    p_tasks = dm.dialog_data['p_task']  # publicators
    index = dm.dialog_data["sync_index"]
    publicator = p_tasks[index]
    sub_grt = f'<b>"{publicator.parse_task.target_name}"</b> ➡️ <b>"{publicator.channel.name}"</b> через бот <b>"{publicator.bot.name}"</b>.'
    greeting = lexicon.GREETINGS['confirm_remove_sync'].format(sub_grt)
    return {
        "greeting": greeting
        }

async def getter_remove_sync(**_kwargs):
    products = []
    user_id = 0
    show_list_panel = False
    not_show_list_panel = not show_list_panel
    try:
        greeting = f'🔗 Выберите какую синхронизацию отменить:'
        dm = _kwargs['dialog_manager']
        #dm.dialog_data['vk_user_name'] = 'None'
        bot = _kwargs['bot']
        event_from_user = _kwargs['event_from_user']
        user_id = event_from_user.id
        #
        user_mld = User.get_user(user_tg_id=user_id)
        publicators = Publicator.select().where(Publicator.user == user_mld)
        sync_num = 0
        for i, p_task in enumerate(publicators, 1):
            sync_num +=1
            sync_str = f'"{p_task.parse_task.target_name}" ➡️  "{p_task.channel.name}"'
            products.append((sync_str, i))
        dm.dialog_data['p_task'] = publicators
    except Exception as ex:
        greeting = '❌ При загрузке данных произошла ошибка, обратитесь к администратору.'
        bots_loger.error(f'Ошибка у пользователя tg_id: {user_id} в getter_remove_sync: {ex}')
        await bot.send_message(user_id, greeting)
        await dm.switch_to(state=states.SG_VKSync.start)
    return {
        "greeting": greeting,
        "user_id": user_id,
        "products": products,
        "show_list_panel": show_list_panel,
        "not_show_list_panel": not_show_list_panel,
        }

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
        publicators = Publicator.select().where(Publicator.user==user_mld)
        sync_str = ''
        for p_task in publicators:
            sync_str = f'{sync_str}\n🔹 <b>"{p_task.parse_task.target_name}"</b> ➡️ <b>"{p_task.channel.name}"</b> через бот <b>"{p_task.bot.name}"</b>.'
        # user_bot_mld = BotModel.get_bot(user=user_mld)
        # channel = Channel.get_channel(user=user_mld)
        # parse_task = ParseTask.get_task(user=user_mld)
        try:
            greeting = f'С возвращением <b>{user_mld.firstname} {user_mld.lastname}</b>! У Вас уже имеются настроенные синхронизации:{sync_str}'
        except Exception as ex:
            greeting = ex
    return {
        "greeting": greeting,
        "is_registered": is_registered,
        "is_not_registered": is_not_registered,
    }

async def getter_contacts(**_kwargs):
    dm = _kwargs['dialog_manager']
    event_from_user = _kwargs['event_from_user']
    user_id = event_from_user.id
    greeting = lexicon.GREETINGS['contact']
    return {
        "greeting": greeting,
    }

async def event_show_contact(callback: CallbackQuery, button: Button,
                    dialog_manager: DialogManager):
    try:
        user_id = callback.from_user.id
        bot = callback.bot
        await bot.send_message(user_id, lexicon.GREETINGS['contact'])
    except:
        pass

async def event_cancel_sync(callback: CallbackQuery, button: Button,
                    dialog_manager: DialogManager):
    # Проверяем зарегистрирован ли пользователь (Заполнил все необходимое для синхронизации)
    user_id = callback.from_user.id
    user_mld = User.get_user(user_tg_id=user_id)
    bot = callback.bot
    #
    p_tasks = dialog_manager.dialog_data['p_task'] # publicators
    index = dialog_manager.dialog_data["sync_index"]
    publicator = p_tasks[index]
    #
    # Проверяем создал ли пользователь бота
    user_bot_mld = publicator.bot
    #
    channel = publicator.channel
    #
    parse_task = publicator.parse_task
    #
    # Получаем парсер
    parser = parse_task.parser
    try:
        criterion = parse_task.criterion
    except:
        criterion = None
    #
    #publicator = Publicator.get_publicator(channel=channel, user=user_mld)
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
        # Получаем количество синхронизаций пользователя.
        user_id = callback.from_user.id
        bot = callback.bot
        user_mld = User.get_user(user_tg_id=user_id)
        publicators_num = Publicator.select().where(Publicator.user==user_mld).count()
        if publicators_num >= NUM_FREE_SYNC:
            await bot.send_message(user_id, '⚠️ В настоящее время количество синхронизаций для пользователе ограничено до 2.')
        else:
            await dialog_manager.start(state=states.SG_enter_token_menu.make_vk_sync)
        pass
    except Exception as ex:
        pass

async def on_product_changed(callback: ChatEvent, select: Any, manager: DialogManager, item_id: str):
    manager.dialog_data["sync_index"] = int(item_id) - 1
    await manager.next()

dialog_interface = (
    Window(
        Format('{greeting}'),
        #SwitchTo(Const(lexicon.BUTTONS['reg']), id="btn_reg", state=SG_enter_token_menu.start, when=F["is_not_registered"]),
        Start(Const(lexicon.BUTTONS['reg']), id="btn_reg", state=states.SG_enter_token_menu.make_vk_sync, on_click=event_make_vk_sync, when=F["is_not_registered"]),
        Button(Const(lexicon.BUTTONS['add_sync']), id="btn_add_sync", on_click=event_make_vk_sync, when=F["is_registered"]),
        #SwitchTo(Const(lexicon.BUTTONS['config']), id="btn_config", state=SG_bot_config.show_menu, when=F["is_registered"]),
        #Start(Const(lexicon.BUTTONS['config']), id="btn_config", state=SG_bot_config.show_menu, when=F["is_registered"]),
        #Button(Const(lexicon.BUTTONS['cancel_sync']), id="btn_cancel_sync", on_click=event_cancel_sync, when=F["is_registered"]),
        SwitchTo(Const(lexicon.BUTTONS['cancel_sync']), id="btn_cancel_sync", state=states.SG_VKSync.remove_sync, when=F["is_registered"]),
        SwitchTo(Const(lexicon.BUTTONS['contacts']), id="btn_contacts", state=states.SG_VKSync.contacts),
        # Start(Const(lexicon.BUTTONS['add_sub']), id="btn_add_sub", state=states.SG_enter_token_menu.make_vk_sync,
        #       on_click=event_make_vk_sync, when=F["is_registered"]),
        getter=getter_start,
        state=states.SG_VKSync.start,
        ),
    Window(
        Format('{greeting}'),
        SwitchTo(Const(lexicon.BUTTONS['назад']), id="btn_back", state=states.SG_VKSync.start),
        getter=getter_contacts,
        state=states.SG_VKSync.contacts,
        ),
    Window(
        Format('{greeting}'),
        ScrollingGroup(
            Select(
                Format("{item[0]}"),
                items="products",
                item_id_getter=itemgetter(1),
                id="w_products",
                on_click=on_product_changed,
            ),
            width=1,
            height=5,
            hide_on_single_page=True,
            id="scroll_with_pager",
        ),
        SwitchTo(Const(lexicon.BUTTONS['назад']), id="btn_back", state=states.SG_VKSync.start),
        getter=getter_remove_sync,
        state=states.SG_VKSync.remove_sync,
        ),
    Window(
        Format('{greeting}'),
        Row(
            SwitchTo(Const(lexicon.BUTTONS['cancel']), id="btn_back", state=states.SG_VKSync.remove_sync),
            Button(Const(lexicon.BUTTONS['confirm']), id="btn_confirm_cancel_sync", on_click=event_cancel_sync),
        ),
        getter=getter_confirm_remove_sync,
        state=states.SG_VKSync.confirm,
    ),
    )

dialog_start_vk_sync = Dialog(*dialog_interface)