from aiogram.types import CallbackQuery, ContentType, Message, FSInputFile, ReplyKeyboardRemove
from aiogram import Bot, Dispatcher, F, Router
from aiogram_dialog import (
    ChatEvent, Dialog, DialogManager, setup_dialogs,
    ShowMode, StartMode, Window,
)
from typing import Any
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Cancel, Button, Row, Select, SwitchTo, Start, Url
from aiogram_dialog.widgets.text import Const, Format, Multi, ScrollingText
from aiogram_dialog.widgets.kbd import (
    CurrentPage, FirstPage, LastPage, Multiselect, NextPage, NumberedPager,
    PrevPage, Row, ScrollingGroup, StubScroll, SwitchTo,
)
from operator import itemgetter
from datetime import datetime
#
from routers.bots.lexicon import *
from routers.parsing.interface_parser import ParseParams
from routers.dispatcher import parsing_dispatcher
from routers.bots.loger import bots_loger
import routers.bots.telegram.states as states
#
from views.telegram.common_dlg_elements import BTN_BACK_WINDOW
#
from models.data.parser import Parser
from models.data.parse_task import ParseTask
from models.data.parse_program import ParseProgram
from models.data.publicator import Publicator, PublicatorModes
from models.data.user import User
from models.data.bot import Bot
from models.data.channel import Channel, ChannelTypes
#
from views.logers import dialogs_loger

async def get_parse_programm(name):
    now_dt = datetime.now().replace(microsecond=0)
    now_dt = now_dt.timestamp()
    parse_program = ParseProgram.get_program(name=name)
    if parse_program == None:
        parse_program = ParseProgram.create(name=name, cr_dt=int(now_dt), img='', user_id=1, description='Единая программа синхронизации телеграм с ВК')
        parse_program.save()
    return parse_program

async def get_channel(channel_id, channel_name, user: User):
    channel = Channel.get_channel(channel_id=channel_id, name=channel_name, user=user)
    if channel == None:
        channel = Channel.create(name=channel_name, user=user, channel_tg_id=channel_id, url='', type=ChannelTypes.Public.value)
        channel.save()
    return channel

async def tg_channel_handler(message: Message, message_input: MessageInput,
                       dialog_manager: DialogManager):
    msg_txt = message.text
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
            dialog_manager.dialog_data['chat_name'] = chat_name
            dialog_manager.dialog_data['chat_id'] = chat_id
            vk_user_name = dialog_manager.dialog_data['vk_user_name']
            group_names = dialog_manager.dialog_data['group_names']
            group_ids = dialog_manager.dialog_data['group_ids']
            filter = dialog_manager.dialog_data['filter']
            group_index = int(dialog_manager.dialog_data["group_index"])
            group_name = group_names[group_index]
            group_id = group_ids[group_index]
            user = User.get_user(user_tg_id=message.from_user.id)
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
            publicator = Publicator.get_publicator(channel_id=chat_id)
            if publicator == None:
                channel = await get_channel(channel_id=chat_id, channel_name=chat_name, user=user)
                publicator = Publicator.create(name=task_name, img='', channel=channel, user=user, parse_task=parse_task, period=30,
                                               mode=PublicatorModes.New.value, range=0, bot=bot_key)
                publicator.save()
            await message.answer(
                f'Телеграм-канал <b>"{chat_name}"</b> ({chat_id}) успешно синхронизирован с ВК <b>"{group_name}"</b>.',
                parse_mode='html')
            await dialog_manager.done()
            #await dialog_manager.start(state=states.SG_bot_config.show_menu, data=dialog_manager.dialog_data)
        except Exception as ex:
            dialogs_loger.error(f'Ошибка tg_channel_handler: {ex}')
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
        bots_loger.error(f'Ошибка getter_start_menu: {ex}')
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
        parser = parsing_dispatcher.get_parser('ВКонтакте')
        group_names = []
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
                        else:
                            group_info = await parser.get_vk_user_info(-group, token)
                            group_name = group_info['full_name']
                            dm.dialog_data['vk_user_name'] = group_name
                    except:
                        group_name = 'None'
                    group_names.append(group_name)
            except:
                groups = []
                await bot.send_message(user_id, 'Группы ВК, которые вы администрируете не обнаружены.')
            pass
        else:
            return 'Парсер не найден'
        for i, gr_name in enumerate(group_names, 1):
            products.append((gr_name, i))
        dm.dialog_data['group_names'] = group_names
        dm.dialog_data['group_ids'] = groups
    except Exception as ex:
        user_id = 0
        bots_loger.error(f'Ошибка getter_start_menu: {ex}')
    try:
        await bot.delete_message(user_id, tmp_msg.message_id)
    except:
        pass
    return {
        "greeting": GREETINGS['выбрать группу ВК'],
        "user_id": user_id,
        "products": products,
        }

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

async def on_filter_changed(callback: ChatEvent, select: Any,
                         manager: DialogManager,
                         item_id: str):
    manager.dialog_data["filter"] = item_id
    await manager.next()

async def event_choose_vk_product(callback: CallbackQuery, button: Button,
                    dialog_manager: DialogManager):
    '''Событие нажатия на кнопку - Назад (возврат в предидущее окно)'''
    await dialog_manager.back()

dialog_bot_config = Dialog(
    Window(
        Format('{greeting}'),
        SwitchTo(Const(BUTTONS['создать синхронизацию']), id="btn_create_assign", state=states.SG_bot_config.create_assign_vk),
        SwitchTo(Const(BUTTONS['удалить синхронизацию']), id="btn_delete_assign", state=states.SG_bot_config.delete_assign),
        SwitchTo(Const(BUTTONS['проверить статус']), id="btn_check_status", state=states.SG_bot_config.check_status),
        SwitchTo(Const(BUTTONS['техническая поддержка']), id="btn_support", state=states.SG_bot_config.support),
        getter=getter_dlg_bot_config,
        state=states.SG_bot_config.show_menu,
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
        #Button(text=Const(BUTTONS['выбрать']), id='btn_check', on_click=event_choose_vk_product),
        BTN_BACK_WINDOW,
        getter=getter_dlg_create_assign_vk,
        state=states.SG_bot_config.create_assign_vk,
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
        #Button(text=Const(BUTTONS['выбрать']), id='btn_check', on_click=event_choose_vk_product),
        BTN_BACK_WINDOW,
        getter=getter_dlg_choose_filter,
        state=states.SG_bot_config.choose_filter,
    ),
    Window(
        Format('{greeting}'),
        MessageInput(tg_channel_handler, content_types=[ContentType.TEXT]),
        BTN_BACK_WINDOW,
        getter=getter_dlg_create_assign_tg,
        state=states.SG_bot_config.create_assign_tg,
    ),
)