from aiogram.types import CallbackQuery, ContentType, Message
from aiogram import Bot
from aiogram.fsm.state import State, StatesGroup
from aiogram_dialog import (
    ChatEvent, Dialog, DialogManager, Window,
)
from typing import Any
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Select
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.kbd import (
    ScrollingGroup, SwitchTo,
)
from operator import itemgetter
from datetime import datetime
#
from views.telegram.vk_sync.lexicon import *
from routers.parsing.parsers_dispatсher import parsers_dispatcher
#
from views.telegram.vk_sync.common_dlg_elements import BTN_BACK_WINDOW
#
from models.data.parser import Parser
from models.data.parse_task import ParseTask
from models.data.parse_program import ParseProgram
from models.data.publicator import Publicator, PublicatorModes
from models.data.user import User
from models.data.bot import Bot
from models.data.channel import Channel
#
from routers.logers import dialogs_loger


class SG_bot_config(StatesGroup):
    show_menu = State()
    create_assign_vk = State()  # создание синхронизации
    choose_filter = State()  # выбор фильтра
    create_assign_tg = State()  # создание синхронизации
    delete_assign = State()  # удаление синхронизации выбор элемента
    delete_assign_execute = State() # попытка удаления
    show_group_list = State()
    support = State()
    check_status = State()

async def get_parse_programm(name):
    now_dt = datetime.now().replace(microsecond=0)
    now_dt = now_dt.timestamp()
    parse_program = ParseProgram.get_program(name=name)
    if parse_program == None:
        parse_program = ParseProgram.create(name=name, cr_dt=int(now_dt), img='', user_id=1, description='Единая программа синхронизации телеграм с ВК')
        parse_program.save()
    return parse_program

async def tg_channel_handler(message: Message, message_input: MessageInput,
                       dialog_manager: DialogManager):
    msg_txt = message.text
    user_id = message.from_user.id
    if message.forward_from_chat != None:
        try:
            now_dt = datetime.now().replace(microsecond=0)
            now_dt = now_dt.timestamp()
            bot_id = dialog_manager.event.bot.id
            bot_key = Bot.get_bot(tg_id=bot_id)
            if bot_key == None:
                bot_key = 0
            chat_name = message.forward_from_chat.full_name
            chat_id = message.forward_from_chat.id
            # Получаем пользователя
            user = User.get_user(user_tg_id=message.from_user.id)
            #ww
            dialog_manager.dialog_data['chat_name'] = chat_name
            dialog_manager.dialog_data['chat_id'] = chat_id
            vk_user_name = dialog_manager.dialog_data['vk_user_name']
            group_names = dialog_manager.dialog_data['group_names']
            group_ids = dialog_manager.dialog_data['group_ids']
            filter = dialog_manager.dialog_data['filter']
            group_index = int(dialog_manager.dialog_data["group_index"])
            group_name = group_names[group_index]
            group_id = group_ids[group_index]
            parser_info = Parser.get_parser(user=user)
            # Получаем программу парсинга
            parse_program =  await get_parse_programm('vk_sync')
            # Создаем задачу
            task_name = f'{vk_user_name}_{group_name}->{chat_name}'
            parse_task = ParseTask.get_task(name=task_name)
            if parse_task == None:
                parse_task = ParseTask.create(name=task_name, program=parse_program, parser=parser_info,
                                          target_id=group_id, target_name=group_name, last_post_id=0,
                                          filter=filter, cr_dt=now_dt, active=1)
                parse_task.save()
            # Создаем публикатор
            channel = Channel.get_channel_or_make(channel_id=chat_id, channel_name=chat_name, user=user)
            publicator = Publicator.get_publicator(channel_id=channel, user=user)
            if publicator == None:
                publicator = Publicator.create(name=task_name, img='', channel=channel, user=user, parse_task=parse_task, period=60,
                                               mode=PublicatorModes.New.value, range=0, bot=bot_key)
                publicator.save()
            await message.answer(
                f'✅ Телеграм-канал <b>"{chat_name}"</b> ({chat_id}) успешно синхронизирован с ВК <b>"{group_name}"</b>.',
                parse_mode='html')
            await dialog_manager.done()
            #await dialog_manager.start(state=states.SG_bot_config.show_menu, data=dialog_manager.dialog_data)
        except Exception as ex:
            dialogs_loger.error(f'Ошибка у пользователя tg_id: {user_id} в getter_start_menu: {ex}')
            await message.answer(f'❌ При создании синхронизации произошла ошибка, обратитесь к администратору.')
            await dialog_manager.done()
    else:
        await message.answer('Я получил сообщение, но это не репост из Вашего канала. '
                       'Пожалуйста перешлите боту любое <b>текстовое</b> сообщение из канала, который необходимо синхронизировать с ВК.', parse_mode='html')
    pass

async def getter_dlg_bot_config(**_kwargs):
    try:
        dm = _kwargs['dialog_manager']
        event_from_user = _kwargs['event_from_user']
        user_id = event_from_user.id
    except Exception as ex:
        user_id = 0
        dialogs_loger.error(f'Ошибка у пользователя tg_id: {user_id} в getter_dlg_bot_config: {ex}')
    return {
        "greeting": GREETINGS['настройка бота'],
        "user_id": user_id,
        }

async def getter_dlg_choose_filter(**_kwargs):
    return {
        "greeting": GREETINGS['выбрать фильтр'],
    }

async def getter_dlg_create_assign_vk(**_kwargs):
    products = []
    try:
        dm = _kwargs['dialog_manager']
        dm.dialog_data['vk_user_name'] = 'None'
        bot = _kwargs['bot']
        event_from_user = _kwargs['event_from_user']
        user = dm.start_data['user']
        user_id = event_from_user.id
        # Формируем список ресурсов для синхронизации
        #products.append((f"Моя стена", 1))
        # Получаем список групп пользователя в ВК
        tmp_msg = await bot.send_message(user_id, 'Получаю данные, подождите....')
        user = User.get_user(user_key=user.id)
        parser_info = Parser.get_parser(user=user)
        token = parser_info.token
        target_id = parser_info.platform_user_id
        parser = parsers_dispatcher.get_parser('ВКонтакте')
        group_names = []
        group_types = []
        if parser != None:
            try:
                res = await parser.get_vk_user_group(target_id, token, 'moder')
                groups_add = res['response']['items']
                # Добавляем стену прльзователя
                #group_names = ['Моя стена']
                groups = [-target_id]
                groups.extend(groups_add)
                # Получаем имена групп
                for group in groups:
                    try:
                        if group > 0:
                            group_info = await parser.get_vk_group_info(group, token)
                            group_name = group_info['name']
                            group_types.append('group')
                        else:
                            group_info = await parser.get_vk_user_info(-group, token)
                            group_name = group_info['full_name']
                            dm.dialog_data['vk_user_name'] = group_name
                            group_types.append('user')
                    except:
                        group_name = 'None'
                    group_names.append(group_name)
            except:
                groups = []
                await bot.send_message(user_id, '⚠️ Группы ВК, которые вы администрируете, не обнаружены.')
                await dm.done()
            pass
        else:
            return 'Парсер не найден'
        for i, gr_name in enumerate(group_names, 1):
            products.append((gr_name, i))
        dm.dialog_data['group_names'] = group_names
        dm.dialog_data['group_ids'] = groups
        dm.dialog_data['group_types'] = groups
        greeting = GREETINGS['выбрать группу ВК']
        try:
            await bot.delete_message(user_id, tmp_msg.message_id)
        except:
            pass
    except Exception as ex:
        user_id = 0
        greeting = '❌ При загрузке данных из ВК произошла ошибка, обратитесь к администратору.'
        dialogs_loger.error(f'Ошибка у пользователя tg_id: {user_id} в getter_dlg_create_assign_vk: {ex}')
        await bot.send_message(user_id, f'❌ При загрузке данных из ВК произошла ошибка, обратитесь к администратору.')
        await dm.done()
    return {
        "greeting": greeting,
        "user_id": user_id,
        "products": products,
        }

async def getter_dlg_delete_assign_choose(**_kwargs):
    products = []
    assigns = []
    greeting = '❌ При загрузке данных о синхронизациях произошла ошибка, обратитесь к администратору.'
    try:
        dm = _kwargs['dialog_manager']
        dm.dialog_data['vk_user_name'] = 'None'
        bot = _kwargs['bot']
        event_from_user = _kwargs['event_from_user']
        user = dm.start_data['user']
        user_id = event_from_user.id
        # Формируем список созданных синхронизаций
        tmp_msg = await bot.send_message(user_id, 'Получаю данные, подождите....')
        # Получаем пользователя
        user = User.get_user(user_key=user.id)
        # Получаем список его синхронизаций
        publicators = Publicator.select().where(Publicator.user==user)
        for i, publicator in enumerate(publicators, 1):
            products.append((publicator.name, i))
            assigns.append(publicator.name)
        dm.dialog_data['assigns'] = assigns
        if len(assigns)>0:
            greeting = GREETINGS['выбрать синхронизацию']
        else:
            greeting = '⚠️ Синхронизации отсутствуют.'
    except Exception as ex:
        user_id = 0
        dialogs_loger.error(f'Ошибка у пользователя tg_id: {user_id} в getter_dlg_delete_assign_choose: {ex}')
        await bot.send_message(user_id, f'❌ При загрузке данных о синхронизациях произошла ошибка, обратитесь к администратору.')
        await dm.done()
    try:
        await bot.delete_message(user_id, tmp_msg.message_id)
    except:
        pass
    return {
        "greeting": greeting,
        "user_id": user_id,
        "products": products,
        }

async def getter_dlg_delete_assign(**_kwargs):
    try:
        dialog_manager = _kwargs['dialog_manager']
        bot = _kwargs['bot']
        event_from_user = _kwargs['event_from_user']
        user_id = event_from_user.id
        assigns = dialog_manager.dialog_data['assigns']
        assign_index = int(dialog_manager.dialog_data["assign_index"])
        assign_name = assigns[assign_index]
        # Удаляем из базы публикатор и задачу
        # Получаем задачу
        publicator = Publicator.get_publicator(name=assign_name)
        if publicator != None:
            task = publicator.parse_task
            publicator.delete_instance()
            task.delete_instance()
        else:
            raise ValueError(f"Не найден публикатор {assign_name}")
        #
        greeting = f'✅ Синхронизация {assign_name} успешно удалена.'
    except Exception as ex:
       greeting = '❌ При удалении синхронизации произошла ошибка, обратитесь к администратору.'
       dialogs_loger.error(f'Ошибка у пользователя tg_id: {user_id} в getter_dlg_delete_assign: {ex}')
       await bot.send_message(user_id,
                              f'❌ При загрузке данных о синхронизациях произошла ошибка, обратитесь к администратору.')
       await dialog_manager.done()
    return {
        "greeting": greeting}

async def getter_dlg_create_assign_tg(**_kwargs):
    products = []
    try:
        dm = _kwargs['dialog_manager']
        bot = _kwargs['bot']
        event_from_user = _kwargs['event_from_user']
        user = dm.start_data['user']
        user_id = event_from_user.id
    except:
        user_id = 0
    return {
        "greeting": GREETINGS['выбрать телеграм-канал'],
        "user_id": user_id,
        "products": products,
        }

async def on_product_changed(callback: ChatEvent, select: Any,
                         manager: DialogManager,
                         item_id: str):
    manager.dialog_data["group_index"] = int(item_id) - 1
    await manager.next()

async def on_product_delete(callback: ChatEvent, select: Any,
                         manager: DialogManager,
                         item_id: str):
    manager.dialog_data["assign_index"] = int(item_id) - 1
    await manager.next()

async def on_filter_changed(callback: ChatEvent, select: Any,
                         manager: DialogManager,
                         item_id: str):
    manager.dialog_data["filter"] = item_id
    await manager.next()

async def event_to_start(callback: CallbackQuery, button: Button,
                    dialog_manager: DialogManager):
    '''Событие нажатия на кнопку - Назад (возврат в предидущее окно)'''
    await dialog_manager.switch_to(SG_bot_config.show_menu)


dialog_bot_config = Dialog(
    Window(
        Format('{greeting}'),
        SwitchTo(Const(BUTTONS['создать синхронизацию']), id="btn_create_assign", state=SG_bot_config.create_assign_vk),
        SwitchTo(Const(BUTTONS['удалить синхронизацию']), id="btn_delete_assign", state=SG_bot_config.delete_assign),
        SwitchTo(Const(BUTTONS['проверить статус']), id="btn_check_status", state=SG_bot_config.check_status),
        SwitchTo(Const(BUTTONS['техническая поддержка']), id="btn_support", state=SG_bot_config.support),
        getter=getter_dlg_bot_config,
        state=SG_bot_config.show_menu,
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
            id="scroll_with_pager",
        ),
        BTN_BACK_WINDOW,
        getter=getter_dlg_create_assign_vk,
        state=SG_bot_config.create_assign_vk,
    ),
    Window(
        Format('{greeting}'),
        Select(
            Format("{item}"),
            items=["all", "owner", "others", "postponed", "suggests", "donut"],
            item_id_getter=lambda x: x,
            id="w_filter",
            on_click=on_filter_changed,
        ),
        BTN_BACK_WINDOW,
        getter=getter_dlg_choose_filter,
        state=SG_bot_config.choose_filter,
    ),
    Window(
        Format('{greeting}'),
        MessageInput(tg_channel_handler, content_types=[ContentType.TEXT]),
        BTN_BACK_WINDOW,
        getter=getter_dlg_create_assign_tg,
        state=SG_bot_config.create_assign_tg,
    ),
    Window(
        Format('{greeting}'),
        ScrollingGroup(
            Select(
                Format("{item[0]}"),
                items="products",
                item_id_getter=itemgetter(1),
                id="w_products",
                on_click=on_product_delete,
            ),
            width=1,
            height=5,
            id="scroll_with_pager",
        ),
        #BTN_BACK_WINDOW,
        Button(text=Const('🔙 Назад'),id='btn_start_window',on_click=event_to_start),
        getter=getter_dlg_delete_assign_choose,
        state=SG_bot_config.delete_assign,
    ),
    Window(
        Format('{greeting}'),
        getter=getter_dlg_delete_assign,
        state=SG_bot_config.delete_assign_execute,
    ),
)