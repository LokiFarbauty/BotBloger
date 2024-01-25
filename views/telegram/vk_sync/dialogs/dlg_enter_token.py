from telegraph import Telegraph
import json
from typing import Any
from operator import itemgetter
from aiogram.types import ContentType, Message
from aiogram import Bot, Dispatcher, F, Router
from aiogram_dialog import (
    Dialog, DialogManager, Window, ChatEvent
)
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import SwitchTo, Start, Next, ScrollingGroup, Button, Select, Url, Cancel
from aiogram_dialog.widgets.text import Const, Format
from routers.parsing.parsers_dispatсher import parsers_dispatcher
from routers.logers import bots_loger
from routers.publicate.publicators import start_publicator_process
from routers.parsing.parsing import parsing
from routers.bots.telegram.bots import BotExt, current_bots
#
from views.telegram.interface_dispather import get_bot_interface
from views.telegram.vk_sync.lexicon import *
from views.telegram.vk_sync import states
#
from models.data.parser import Parser
from models.data.user import User
from models.data.parse_task import ParseTask, ParseTaskStates, ParseTaskActive, ParseModes
from models.data.publicator import Publicator, PublicatorStates, PublicatorModes
from models.data.channel import Channel, ChannelTypes
from models.data.criterion import Criterion
from models.data.bot import Bot as BotModel, BotDestination
#
from datetime import datetime



async def get_user_id(user_name, token):
    user_id = 0 # 0 - не правильный токен
    parser = parsers_dispatcher.get_parser('ВКонтакте')
    if parser != None:
        user_id = await parser.get_vk_object_id(user_name, token)
    else:
        user_id = -1 # ошибка парсера
    return user_id

async def is_vk_token_good(token: str) -> bool:
    parser = parsers_dispatcher.get_parser('ВКонтакте')
    if parser != None:
        res = await parser.check_token(token)
        return res
    return False

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


async def bot_token_handler(message: Message, message_input: MessageInput,
                       dialog_manager: DialogManager):
    bot_token = message.text
    # Проверяем токен
    if bot_token.find(':') == -1:
        await message.answer(f'❌ <b>"{bot_token}"</b> - не является токеном телеграм-бота.')
        return
    # Проверяем токен на уникальность
    # bot_mld = BotModel.get_bot(token=bot_token)
    # if bot_mld != None:
    #     await message.answer(
    #         f'❌ <b>"{bot_token}"</b> - данный бот уже используется для администрирования канала. Если он принадлежит Вам, пожалуйста напишите администратору.')
    #     return
    # Проверка бота
    try:
        test_bot = Bot(token=bot_token)
        bot_info = await test_bot.get_me()
        bot_name = bot_info.first_name
        bot_url = bot_info.username
        dialog_manager.dialog_data['bot_name'] = bot_name
        dialog_manager.dialog_data['bot_url'] = bot_url
    except Exception as ex:
        await message.answer(
            f'❌ Ошибка связи с ботом <b>"{bot_token}"</b>: {ex}')
        return
    # Токен подходит
    dialog_manager.dialog_data['bot_token']=bot_token
    #await dialog_manager.start(state=SG_enter_token_menu.get_user_id, data=dialog_manager.dialog_data)
    await dialog_manager.next()

async def get_channel_handler(message: Message, message_input: MessageInput,
                       dialog_manager: DialogManager):
    try:
        channel_id = message.forward_from_chat.id
        channel_name = message.forward_from_chat.full_name
        channel_url = f't.me/{message.forward_from_chat.username}'
        dialog_manager.dialog_data['channel_id'] = channel_id
        dialog_manager.dialog_data['channel_name'] = channel_name
        dialog_manager.dialog_data['channel_url'] = channel_url
        await dialog_manager.next()
    except Exception as ex:
        await message.answer(f'❌ Это не является репостом из канала. Пожалуйста отправьте мне любой репост из канала.')
        return

async def vk_token_handler(message: Message, message_input: MessageInput,
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
            if end_t_pos == -1:
                end_t_pos = len(ac_url)
            access_token = ac_url[t_pos+len('access_token='):end_t_pos]
        dialog_manager.dialog_data['access_token'] = access_token
        # Проверяем токен
        if not await is_vk_token_good(access_token):
            await message.answer('❌ Введен неработоспособный токен.')
            return
        #dialog_manager.reset_stack()
        # получаем пользователя
        t_pos = ac_url.find('user_id=')
        if t_pos == -1:
            #await message.answer(GREETINGS['нет токена'])
            await dialog_manager.switch_to(state=states.SG_enter_token_menu.get_user_id)
            return
        end_t_pos = ac_url.find('&', t_pos)
        vk_user_id = ac_url[t_pos + len('user_id='):end_t_pos]
        dialog_manager.dialog_data['vk_user_id'] = vk_user_id
        # Вызываем диалог завершения
        await dialog_manager.switch_to(states.SG_enter_token_menu.create_assign_vk)
        #parser = await get_parser(message.from_user.id, access_token, vk_user_id)
        #await message.answer(f'Парсер: {parser.name}')
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
        access_token = dialog_manager.dialog_data['access_token']
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
        elif user_id == None:
            await message.answer('Ошибка: введен не верный токен.')
            await dialog_manager.back()
        else:
            dialog_manager.dialog_data['vk_user_id'] = user_id
            #await dialog_manager.switch_to(SG_enter_token_menu.make_vk_sync_final)
            await dialog_manager.next()
            #parser = await get_parser(message.from_user.id, access_token, user_id)
            #await message.answer(f'Парсер: {parser.name}')
    except Exception as ex:
        await message.answer(GREETINGS['ошибка'])
        return


async def getter_make_vk_sync(**_kwargs):
    return {
        "greeting": GREETINGS['make_vk_sync'],
    }

async def getter_make_bot(**_kwargs):
    dm = _kwargs['dialog_manager']
    bot = _kwargs['bot']
    event_chat = _kwargs['event_chat']
    try:
        user = dm.dialog_data['user']
        user_name = f'{user.firstname} {user.lastname}'
    except:
        user_name = ''
    return {
        "greeting": GREETINGS['make_bot_grt'].format(user_name),
        }

async def getter_get_channel(**_kwargs):
    return {
        "greeting": GREETINGS['выбрать телеграм-канал'],
    }

async def getter_make_vk_token(**_kwargs):
    return {
        "greeting": GREETINGS['make_vk_token'],
    }

async def getter_why_bot(**_kwargs):
    return {
        "greeting": GREETINGS['why_bot'],
    }

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

async def getter_vk_sync_final(**_kwargs):
    greeting = GREETINGS['vk_sync_final']
    dm = _kwargs['dialog_manager']
    bot = _kwargs['bot']
    event_chat = _kwargs['event_chat']
    try:
        bot_token = dm.dialog_data['bot_token']
        access_vk_token = dm.dialog_data['access_token']
        bot_name = dm.dialog_data['bot_name']
        bot_url = dm.dialog_data['bot_url']
        channel_name = dm.dialog_data['channel_name']
        channel_url = dm.dialog_data['channel_url']
        group_names = dm.dialog_data['group_names']
        group_ids = dm.dialog_data['group_ids']
        group_index = int(dm.dialog_data["group_index"])
        group_name = group_names[group_index]
        greeting = f'{greeting}🤖 Бот: <b>"{bot_name}" ({bot_url}).</b>'
        greeting = f'{greeting}\n⭐️ VKToken: <b>"проверен".</b>'
        greeting = f'{greeting}\n⬅️ Ресурс ВК: <b>"{group_name}".</b>'
        greeting = f'{greeting}\n➡️ Канал: <b>"{channel_name}" ({channel_url}).</b>'
    except Exception as ex:
        bots_loger.error(f'Ошибка при создании синхронизации. Пользователь (tg_id) <{event_chat.id}>. Ошибка: {ex}')
        greeting = 'Ошибка создания синхронизации. Пожалуйста сообщите о проблеме администратору.'
    return {
        "greeting": greeting,
    }

async def getter_dlg_create_assign_vk(**_kwargs):
    products = []
    try:
        dm = _kwargs['dialog_manager']
        dm.dialog_data['vk_user_name'] = 'None'
        bot = _kwargs['bot']
        event_from_user = _kwargs['event_from_user']
        user_id = event_from_user.id
        user = User.get_user(user_tg_id=user_id)
        # Формируем список ресурсов для синхронизации
        #products.append((f"Моя стена", 1))
        # Получаем список групп пользователя в ВК
        tmp_msg = await bot.send_message(user_id, 'Получаю данные, подождите....')
        #user = User.get_user(user_key=user.id)
        token = dm.dialog_data['access_token']
        target_id = int(dm.dialog_data['vk_user_id'])
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
            except Exception as ex:
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
        dm.dialog_data['group_types'] = group_types
        greeting = GREETINGS['выбрать группу ВК']
        try:
            await bot.delete_message(user_id, tmp_msg.message_id)
        except:
            pass
    except Exception as ex:
        user_id = 0
        greeting = '❌ При загрузке данных из ВК произошла ошибка, обратитесь к администратору.'
        bots_loger.error(f'Ошибка у пользователя tg_id: {user_id} в getter_dlg_create_assign_vk: {ex}')
        await bot.send_message(user_id, f'❌ При загрузке данных из ВК произошла ошибка, обратитесь к администратору.')
        await dm.done()
    return {
        "greeting": greeting,
        "user_id": user_id,
        "products": products,
        }

async def getter_vk_sync_maked(**_kwargs):
    greeting = GREETINGS['sync_maked']
    set_admin_url = ''
    dm = _kwargs['dialog_manager']
    bot = _kwargs['bot']
    event_chat = _kwargs['event_chat']
    try:
        user_id = event_chat.id
        user_mld = User.get_user(user_tg_id=user_id)
        bot_token = dm.dialog_data['bot_token']
        bot_name = dm.dialog_data['bot_name']
        bot_url = dm.dialog_data['bot_url']
        access_vk_token = dm.dialog_data['access_token']
        vk_user_id = dm.dialog_data['vk_user_id']
        channel_id = dm.dialog_data['channel_id']
        channel_name = dm.dialog_data['channel_name']
        channel_url = dm.dialog_data['channel_url']
        group_names = dm.dialog_data['group_names']
        group_ids = dm.dialog_data['group_ids']
        group_index = int(dm.dialog_data["group_index"])
        group_types = dm.dialog_data['group_types']
        group_name = group_names[group_index]
        vk_group_id = group_ids[group_index]
        group_type = group_types[group_index]
        set_admin_url = f'tg://resolve?domain={bot_url}&startchannel&admin=invite_users+post_messages+edit_messages+delete_messages'
        bot_options={}
        # Проверяем, что выбранный ВК ресурс уже не был добавлен
        check_task = ParseTask.get_task(user=user_mld, target_id=vk_group_id)
        if check_task != None:
            await bot.send_message(user_id, f'"{group_name}" уже синхронизирована.')
        # Получаем токен telepra.ph
        telegraph = Telegraph()
        telegraph_account = telegraph.create_account(user_mld.username, bot.name, f'https://t.me/{bot.url}')
        telegraph_token = telegraph_account['access_token']
        telegraph_auth = telegraph_account['auth_url']
        bot_options['telegraph_token'] = telegraph_token
        bot_options['telegraph_auth'] = telegraph_auth
        # Добавляем пользовательский бот
        bot_mld = BotModel.make(user=user_mld, token=bot_token, parse_mode='HTML', name=bot_name, url=bot_url, active=1, public=0, tg_id=0, db_file='')
        bot_mld.interface = 'VKSync'
        bot_mld.destination = BotDestination.VKSync.value
        bot_mld.options = json.dumps(bot_options)
        bot_mld.save()
        # Создаем парсер
        parser = Parser.get_parser(user=user_mld, token=access_vk_token, platform_user_id=vk_user_id)
        if parser == None:
            parser = await get_parser(user_id, access_vk_token, vk_user_id)
        # Создаем канал
        channel = Channel.get_channel(user=user_mld, channel_id=channel_id)
        if channel == None:
            channel = Channel.create(channel_tg_id=channel_id, name=channel_name, url=channel_url, user=user_mld, type=ChannelTypes.VkSync.value)
        # Создаем задачу парсинга
        program = None
        vk_filter='all'
        dt = datetime.now()
        cr_dt = dt.replace(microsecond=0).timestamp()
        task_name = f'{user_mld.username}_{group_name}->{bot_name}'
        parse_task = ParseTask.get_task(name=task_name, user=user_mld)
        if parse_task == None:
            criterion = Criterion.create(target_id=vk_group_id,
                                          target_name=group_name, target_type=group_type, post_max_text_length=50000, post_start_date=cr_dt)
            task = ParseTask.create(name=task_name, user=user_mld, program=program, parser=parser, criterion=criterion,
                                    target_id=vk_group_id,
                                    target_name=group_name, target_type=group_type, filter=vk_filter,
                                    cr_dt=cr_dt, post_num='all', state=ParseTaskStates.Stopped.value,
                                    last_post_id=0, mode=ParseModes.New.value,
                                    active=ParseTaskActive.InWork.value, period=10*60)
        else:
            await bot.send_message(user_id,
                                   f'❌ При синхронизации произошла ошибка (задача уже существует), обратитесь к администратору.')
            bot_mld.delete_instance()
            return
        # Создаём публикатор
        publicator = Publicator.get_publicator(name=task_name, channel=channel, user=user_mld)
        if publicator == None:
            pub_criterion = Criterion.create(target_id=task.target_id,
                                         target_name=task.target_name, target_type=task.target_type)
            publicator = Publicator.create(name=task_name, img='', channel=channel, user=user_mld,
                                           parse_task=task, criterion=pub_criterion, mode=PublicatorModes.New.value,
                                           period=5*60, bot=bot_mld, delete_public_post=1,
                                           telegraph_token=telegraph_token, author_caption='', author_name=bot.name,
                                           cr_dt=cr_dt, autostart=1, start_public_hour=0, end_public_hour=23,
                                           author_url=f'https://t.me/{bot.url}', premoderate=0,
                                           state=PublicatorStates.Working.value)
        else:
            await bot.send_message(user_id,
                                   f'❌ При синхронизации произошла ошибка (публикатор уже существует), обратитесь к администратору.')
            bot_mld.delete_instance()
            criterion.delete_instance()
            parse_task.delete_instance()
            return
        # Запускаем бот
        try:
            pass
            if bot_mld.interface == None:
                bot_mld.interface = 'None'
            Bot_interface = get_bot_interface(bot_mld.interface)
            bot_interface = Bot_interface()
            bot = BotExt(token=bot_mld.token, parse_mode=bot_mld.parse_mode, active=bot_mld.active, public=bot_mld.public, dispatcher=bot_interface.dp)
            current_bots.append(bot)
            await bot.start_polling_task()
            bots_loger.info(f'Вновь созданный пользователем <{user_mld.username}> бот <{bot.name}> запущен.')
        except Exception as ex:
            bots_loger.error(
                f'Ошибка запуска созданного пользователем <{user_mld.username}> бота <{bot_mld.name}> (key: {bot_mld.get_id()}). Ошибка: {ex}')
        # Запускаем задачу парсеринга
        try:
            pass
            res = await parsers_dispatcher.start_task(task_key=task.get_id(), func=parsing)
            bots_loger.info(res)
        except Exception as ex:
            bots_loger.error(
                f'Ошибка запуска вновь созданной задачи <{task.name}> (key: {task.get_id()}). Ошибка: {ex}')
        # Запускаем публикатор
        try:
            res=start_publicator_process(publicator)
            bots_loger.info(f'{res}')
            pass
        except Exception as ex:
            bots_loger.error(f'Ошибка запуска вновь созданного публикатора <{publicator.name}> (key: {publicator.get_id()}). Ошибка: {ex}')
    except Exception as ex:
        bots_loger.error(f'Ошибка создания синхронизации. Пользователь (tg_id) <{user_id}>. Ошибка: {ex}')
        greeting = f'Ошибка синхронизации. Пожалуйста сообщите о проблеме администратору.'
    return {
        "greeting": greeting,
        "set_admin_url": set_admin_url,
    }

async def on_product_changed(callback: ChatEvent, select: Any, manager: DialogManager, item_id: str):
    manager.dialog_data["group_index"] = int(item_id) - 1
    await manager.next()

dialog_interface=(Window(
        Format('{greeting}'),
        Next(Const(BUTTONS['start_make_sync']), id="btn_start_make_sync"),
        getter=getter_make_vk_sync,
        state=states.SG_enter_token_menu.make_vk_sync,
    ),
    Window(
        Format('{greeting}'),
        MessageInput(bot_token_handler, content_types=[ContentType.TEXT]),
        SwitchTo(Const(BUTTONS['why_bot']), id="btn_why_bot", state=states.SG_enter_token_menu.why_bot),
        SwitchTo(Const(BUTTONS['to_start']), id="btn_main_menu", state=states.SG_enter_token_menu.make_vk_sync),
        getter=getter_make_bot,
        state=states.SG_enter_token_menu.make_bot,
    ),
    Window(
        Format('{greeting}'),
        MessageInput(get_channel_handler, content_types=[ContentType.TEXT]),
        SwitchTo(Const(BUTTONS['назад']), id="btn_back", state=states.SG_enter_token_menu.make_bot),
        getter=getter_get_channel,
        state=states.SG_enter_token_menu.get_channel,
    ),
    Window(
        Format('{greeting}'),
        MessageInput(vk_token_handler, content_types=[ContentType.TEXT]),
        SwitchTo(Const(BUTTONS['зачем токен']), id="btn_why_token", state=states.SG_enter_token_menu.why_token),
        SwitchTo(Const(BUTTONS['как получить токен']), id="btn_where_token", state=states.SG_enter_token_menu.where_token),
        SwitchTo(Const(BUTTONS['у меня есть токен']), id="btn_token_got", state=states.SG_enter_token_menu.token_got),
        SwitchTo(Const(BUTTONS['назад']), id="btn_back", state=states.SG_enter_token_menu.get_channel),
        getter=getter_make_vk_token,
        state=states.SG_enter_token_menu.get_vk_token,
    ),
    Window(
        Format('{greeting}'),
        MessageInput(vk_token_handler, content_types=[ContentType.TEXT]),
        #Back(Const(BUTTONS['назад']), id="btn_getter_token_got_back"),
        SwitchTo(Const(BUTTONS['назад']), id="btn_back", state=states.SG_enter_token_menu.get_vk_token),
        getter=getter_token_got,
        state=states.SG_enter_token_menu.token_got,
    ),
    Window(
        Format('{greeting}'),
        MessageInput(user_id_handler, content_types=[ContentType.TEXT]),
        #Back(Const(BUTTONS['назад']), id="btn_get_user_id_back"),
        SwitchTo(Const(BUTTONS['назад']), id="btn_back", state=states.SG_enter_token_menu.token_got),
        getter=getter_user_id,
        state=states.SG_enter_token_menu.get_user_id,
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
        SwitchTo(Const(BUTTONS['назад']), id="btn_back", state=states.SG_enter_token_menu.get_vk_token),
        getter=getter_dlg_create_assign_vk,
        state=states.SG_enter_token_menu.create_assign_vk,
    ),
    Window(
        Format('{greeting}'),
        # Back(Const(BUTTONS['назад']), id="btn_get_user_id_back"),
        SwitchTo(Const(BUTTONS['make_sync']), id="btn_make_sync", state=states.SG_enter_token_menu.vk_sync_maked),
        SwitchTo(Const(BUTTONS['назад']), id="btn_back", state=states.SG_enter_token_menu.create_assign_vk),
        getter=getter_vk_sync_final,
        state=states.SG_enter_token_menu.make_vk_sync_final,
    ),
    Window(
        Format('{greeting}'),
        Url(text=Const('Сделать бота админом'), url=Format('{set_admin_url}'), id="url_set_admin"),
        # Back(Const(BUTTONS['назад']), id="btn_get_user_id_back"),
        #SwitchTo(Const(BUTTONS['назад']), id="btn_back", state=SG_enter_token_menu.get_vk_token),
        Cancel(Const('Закончить настройку'), id="btn_cancel"),
        getter=getter_vk_sync_maked,
        state=states.SG_enter_token_menu.vk_sync_maked,
    ),
    Window(
        Format('{greeting}'),
        # Back(Const(BUTTONS['назад']), id="btn_why_token_back"),
        SwitchTo(Const(BUTTONS['назад']), id="btn_back", state=states.SG_enter_token_menu.make_bot),
        getter=getter_why_bot,
        state=states.SG_enter_token_menu.why_bot,
    ),
    Window(
        Format('{greeting}'),
        # Back(Const(BUTTONS['назад']), id="btn_why_token_back"),
        SwitchTo(Const(BUTTONS['назад']), id="btn_back", state=states.SG_enter_token_menu.get_vk_token),
        getter=getter_why_token,
        state=states.SG_enter_token_menu.why_token,
    ),
    Window(
        Format('{greeting}'),
        # Back(Const(BUTTONS['назад']), id="btn_where_token_back"),
        SwitchTo(Const(BUTTONS['назад']), id="btn_back", state=states.SG_enter_token_menu.get_vk_token),
        getter=getter_where_token,
        state=states.SG_enter_token_menu.where_token,
    ))

dialog_start_menu = Dialog(*dialog_interface)