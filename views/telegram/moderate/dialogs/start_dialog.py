'''В этом диалоге должно определятся зарегистрирован ли пользователь, либо нужно пройти процедуру регистрации'''
#1
from operator import itemgetter
from typing import Any
from aiogram.types import CallbackQuery, ContentType, Message, FSInputFile
from aiogram_dialog import (
    Dialog, DialogManager, Window, ChatEvent, StartMode
)
from aiogram import Bot, Dispatcher, F, Router
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import SwitchTo, Start, Next, ScrollingGroup, Button, Select, Url, Cancel, Row, NumberedPager, Back
from aiogram_dialog.widgets.media import StaticMedia
from aiogram_dialog.widgets.text import Const, Format, Multi, ScrollingText
# routers
from routers.logers import bots_loger
from routers.parsing.parsers_dispatсher import parsers_dispatcher
from routers.publicate.publicators import stop_publicator_process
import routers.bots.telegram.bots as bots_unit
# views
import views.telegram.moderate.lexicon as lexicon
# models
from models.data.user import User
from models.data.photo import Photo
from models.data.post import Post, ModerateStates
from models.data.post_text_FTS import PostText
from models.data.user_bot import User_Bot
from models.data.bot import Bot as BotModel
from models.data.user_parse_program import User_ParseProgram
from models.data.parse_task import ParseTask, ParseTaskStates, ParseTaskActive
from models.data.publicator import Publicator, PublicatorStates, PublicatorModes
from models.data.channel import Channel, ChannelTypes
from models.data.criterion import Criterion
# other
from datetime import datetime
# dialogs
from views.telegram.moderate import states, common_dlg_elements
import translators as ts


MAX_TEXT_SIZE = 650

def get_lang_img(lang_code='ru'):
    if lang_code == 'ru':
        return '🇷🇺'
    elif lang_code == 'en':
        return '🇬🇧'
    elif lang_code == 'de':
        return '🇩🇪'
    elif lang_code == 'zh-Hans':
        return '🇨🇳'
    elif lang_code == 'es':
        return '🇪🇸'
    elif lang_code == 'hi':
        return '🇮🇳'
    elif lang_code == 'pt':
        return '🇵🇹'
    elif lang_code == 'fr':
        return '🇫🇷'
    elif lang_code == 'uk':
        return '🇺🇦'
    elif lang_code == 'ko':
        return '🇰🇷'
    elif lang_code == 'pl':
        return '🇵🇱'
    elif lang_code == 'tr':
        return '🇹🇷'
    else:
        return '🏳️'


async def getter_ads(**_kwargs):
    dm = _kwargs['dialog_manager']
    event_from_user = _kwargs['event_from_user']
    user_id = event_from_user.id
    greeting = 'Данный бот используется для синхронизации. ' \
               'Если Вам необходим авторепостинг из <b>ВКонтакте</b> в <b>Телеграм</b> можете воспользоваться <a href="https://t.me/VK_sync_tg_bot">синхроботом 🤖</a>.'
    return {
        "greeting": greeting,
    }

async def getter_scheme(**_kwargs):
    dm = _kwargs['dialog_manager']
    event_from_user = _kwargs['event_from_user']
    user_id = event_from_user.id
    greeting = '<b>Программы:</b>\n'
    # Получаем список каналов в котырые назначен постинг
    user_programs = dm.dialog_data['programs']
    for i, user_program in enumerate(user_programs, 1):
        greeting = f'{greeting}{i}. "{user_program.name}":\n'
        # Получаем задачи
        parse_tasks = ParseTask.select().where((ParseTask.program == user_program) & (ParseTask.active == 1))
        for parse_task in parse_tasks:
            greeting = f'{greeting}  <b>"{parse_task.target_name}"</b>(VK) -> \n'
            target = ''
            # Получаем публикаторы
            publicators = Publicator.select().where(Publicator.parse_program == user_program)
            for publicator in publicators:
                target = f'{target}    <b>"{publicator.channel.name}"</b>(TG)\n'
            publicators = Publicator.select().where(Publicator.parse_task == parse_task)
            for publicator in publicators:
                target = f'{target}    <b>"{publicator.channel.name}"</b>(TG)\n'
            greeting = f'{greeting}{target}'
    return {
        "greeting": greeting
        }

async def getter_programm(**_kwargs):
    products = []
    user_id = 0
    try:
        greeting = f'Выберите программу:'
        dm = _kwargs['dialog_manager']
        #dm.dialog_data['vk_user_name'] = 'None'
        bot = _kwargs['bot']
        event_from_user = _kwargs['event_from_user']
        user_id = event_from_user.id
        #
        user_mld = User.get_user(user_tg_id=user_id)
        user_programs = dm.dialog_data['programs']
        for i, user_program in enumerate(user_programs, 1):
            products.append((user_program.name, i))
    except Exception as ex:
        greeting = '❌ При загрузке данных произошла ошибка, обратитесь к администратору.'
        bots_loger.error(f'Ошибка у пользователя tg_id: {user_id} в getter_programm: {ex}')
        await bot.send_message(user_id, greeting)
        await dm.switch_to(state=states.SG_Main.start)
    return {
        "greeting": greeting,
        "user_id": user_id,
        "products": products,
        }

async def check_user_program(user_tg_id: int):
    # Проверяем зарегистрирован ли пользователь (доступна ли ему модерация в програмах)
    user_mld = User.get_user(user_tg_id=user_tg_id)
    # Проверяем есть ли доступные пользователю программы
    user_programs_mlds = User_ParseProgram.select().where(User_ParseProgram.user==user_mld).order_by(User_ParseProgram.program.asc())
    user_programs = []
    for user_program in user_programs_mlds:
        user_programs.append(user_program.program)
    return user_programs

async def getter_start(**_kwargs):
    dm = _kwargs['dialog_manager']
    event_from_user = _kwargs['event_from_user']
    user_id = event_from_user.id
    user_programs = await check_user_program(user_tg_id=user_id)
    if len(user_programs) > 0:
        greeting = lexicon.GREETINGS['main_menu_grt'].format(username=event_from_user.full_name)
        dm.dialog_data['programs'] = user_programs
        is_registered = True
    else:
        greeting = lexicon.GREETINGS['main_menu_no_program_grt'].format(username=event_from_user.full_name, bots_channels=lexicon.bots_channels)
        is_registered = False
    return {
        "greeting": greeting,
        "is_registered": is_registered,
    }

async def getter_reference(**_kwargs):
    dm = _kwargs['dialog_manager']
    event_from_user = _kwargs['event_from_user']
    user_id = event_from_user.id
    greeting = lexicon.GREETINGS['reference']
    return {
        "greeting": greeting,
    }

async def getter_language(**_kwargs):
    dm = _kwargs['dialog_manager']
    event_from_user = _kwargs['event_from_user']
    user_id = event_from_user.id
    greeting = lexicon.GREETINGS['language']
    return {
        "greeting": greeting,
    }

async def getter_post_utilities(**_kwargs):
    dm = _kwargs['dialog_manager']
    event_from_user = _kwargs['event_from_user']
    user_id = event_from_user.id
    greeting = lexicon.GREETINGS['utilities']
    return {
        "greeting": greeting,
    }

async def getter_show_post_for_view(**_kwargs):
    # Получаем модель
    bot = _kwargs['bot']
    user_id = _kwargs['event_from_user'].id
    context = _kwargs['aiogd_context']
    dialog_manager = _kwargs['dialog_manager']
    dialog_manager.dialog_data['aiogd_context'] = context
    data = dialog_manager.dialog_data
    img_url = ''
    lang_img = '🏳️'
    img_exist = False
    user_mld = User.get_user(user_tg_id=user_id)
    # Загружаем посты из выбранной программы для рассмотрения
    try:
        program_index = data["program_index"]
    except:
        program_index = -1
    user_programs = data['programs']
    #tmp_msg = await bot.send_message(user_id, 'Получаю данные, подождите....')
    # Получаем количество постов
    if program_index >= 0:
        checked_program = user_programs[program_index]
        posts_count = Post.select().where((Post.parse_program == checked_program) & (Post.moderate == ModerateStates.NotVerified.value)).count()
        posts = Post.select().where((Post.parse_program == checked_program) & (Post.moderate == ModerateStates.NotVerified.value)).order_by(Post.dt.asc())
    else:
        user_programs = User_ParseProgram.select(User_ParseProgram.program).where(User_ParseProgram.user == user_mld)
        posts_count = Post.select().where((Post.parse_program.in_(user_programs)) & (Post.moderate == ModerateStates.NotVerified.value)).count()
        posts = Post.select().where((Post.parse_program.in_(user_programs)) & (Post.moderate == ModerateStates.NotVerified.value)).order_by(Post.dt.asc())
    # Получаем сдвиг
    try:
        offset = data['offset']
    except:
        offset = 0
        data['offset'] = 0
    # Проверяем ограничение диапазона
    if offset>=posts_count:
        offset-=1
        data['offset'] = offset
    try:
        if offset == 14:
            pass
        #start = time.time()
        # Получаем текст поста
        post = posts[offset]
        lang_img = get_lang_img(post.translation)
        post_text_id = post.text
        post_text_mld = PostText.get_by_id(post_text_id)
        post_text = post_text_mld.text
        # При необходимостьи переводим текст
        try:
            if post.translation != 'ru':
                translators_lst = ['bing', 'google', 'yandex', 'baidu', 'deepl']
                for translator in translators_lst:
                    try:
                        post_text = ts.translate_text(post_text, translator=translator, to_language=post.translation)
                        break
                    except Exception as ex:
                        pass
        except Exception as ex:
            bots_loger.warning(f'Не удалось перевести текст {post_text_id} на язык {post.translation}. Ошибка: {ex}')
        # Получаем описание
        data['post_text_id'] = post_text_id
        data['post'] = post
        try:
            imgs_mlds = Photo.select().where(Photo.owner == post)
            img_url = imgs_mlds[0].url
            img_exist = True
        except:
            img_exist = False
        data['post'] = post
        post_desc = await common_dlg_elements.get_post_desc(post, post_text, offset, user_mld, posts_count, debug=True)
        # end = time.time()
        # print(f'\nВремя операции - {end - start} сек.')
    except Exception as ex:
        if offset>0:
            offset = 0
            data['offset'] = offset
            try:
                post_desc = await common_dlg_elements.get_post_desc(post, post_text, offset, user_mld, posts_count)
            except:
                post_text = '_'
                post_desc = common_dlg_elements.PostDesc(POST_TEXT='_', POST_DESC=lexicon.GREETINGS['no_post_for_view'], POST_EXIST=False)
        else:
            post_text = '_'
            post_desc = common_dlg_elements.PostDesc(POST_TEXT='_', POST_DESC=lexicon.GREETINGS['no_post_for_view'], POST_EXIST=False)
    text_len = len(post_text)
    if text_len >= MAX_TEXT_SIZE:
        post_big = True
    else:
        post_big = False
    # Возвращаем значения
    # try:
    #     await bot.delete_message(user_id, tmp_msg.message_id)
    # except:
    #     pass
    return {
        "offset": offset,
        "lang_img": lang_img,
        "post_desc": post_desc.POST_DESC,
        "post_text": post_desc.POST_TEXT,
        "post_exist": post_desc.POST_EXIST,
        "post_not_exist": not post_desc.POST_EXIST,
        "post_big": post_big,
        'img_url': img_url,
        "img_exist": img_exist,
    }


async def on_product_changed(callback: ChatEvent, select: Any, manager: DialogManager, item_id: str):
    manager.dialog_data["program_index"] = int(item_id) - 1
    await manager.next()

async def reset_program_index(callback: CallbackQuery, button: Button,
                    dialog_manager: DialogManager):
    dialog_manager.dialog_data["program_index"] = -1

dialog_interface = (
    Window(
        Format('{greeting}'),
        SwitchTo(Const(lexicon.BUTTONS['for_viewing']), id="btn_for_viewing", state=states.SG_Main.for_viewing, on_click=reset_program_index, when=F["is_registered"]),
        SwitchTo(Const(lexicon.BUTTONS['programm']), id="btn_programm", state=states.SG_Main.programm, when=F["is_registered"]),
        SwitchTo(Const(lexicon.BUTTONS['scheme']), id="btn_scheme", state=states.SG_Main.scheme, when=F["is_registered"]),
        SwitchTo(Const(lexicon.BUTTONS['reference']), id="btn_reference", state=states.SG_Main.reference, when=F["is_registered"]),
        # Start(Const(lexicon.BUTTONS['reg']), id="btn_reg", state=states.SG_enter_token_menu.make_vk_sync, on_click=event_make_vk_sync, when=F["is_not_registered"]),
        # Button(Const(lexicon.BUTTONS['add_sync']), id="btn_add_sync", on_click=event_make_vk_sync, when=F["is_registered"]),
        # Start(Const(lexicon.BUTTONS['add_sub']), id="btn_add_sub", state=states.SG_enter_token_menu.make_vk_sync,
        #       on_click=event_make_vk_sync, when=F["is_registered"]),
        getter=getter_start,
        state=states.SG_Main.start,
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
        SwitchTo(Const(lexicon.BUTTONS['назад']), id="btn_back", state=states.SG_Main.start),
        getter=getter_programm,
        state=states.SG_Main.programm,
        ),
    Window(
        StaticMedia(
            url=Format('{img_url}'),
            type=ContentType.PHOTO,
            when=F["img_exist"]
        ),
        Format('{post_desc}'),
        ScrollingText(
            text=Format('{post_text}'),
            id='text_scroll_post',
            page_size=MAX_TEXT_SIZE,
            when=F["post_exist"]
        ),
        ScrollingGroup(
            NumberedPager(
                scroll='text_scroll_post',
            ),
            id='sgrp_scroll_post',
            width=8,
            height=1,
            hide_on_single_page=True,
            when=F["post_big"],
        ),
        Row(
            common_dlg_elements.PREV_CASE_BUTTON,
            SwitchTo(Const('⏏️'), id="btn_back", state=states.SG_Main.programm),
            #common_dlg_elements.BTN_BACK,
            SwitchTo(Const('⚙️'), id="btn_post_utilities", state=states.SG_Main.post_utilities),
            common_dlg_elements.DEL_POST_BUTTON,
            #common_dlg_elements.SHOW_SAME_POST,
            common_dlg_elements.SKIP_POST_BUTTON,
            SwitchTo(Format('{lang_img}'), id="btn_langs", state=states.SG_Main.language),
            common_dlg_elements.PUBLIC_POST_BUTTON,
            common_dlg_elements.NEXT_CASE_BUTTON,
            when=F["post_exist"]
        ),
        SwitchTo(Const(lexicon.BUTTONS['назад']), id="btn_back", state=states.SG_Main.programm, when=F["post_not_exist"]),
        # common_elements.MAIN_MENU_BUTTON,
        getter=getter_show_post_for_view,
        state=states.SG_Main.for_viewing,
    ),
    Window(
        Format('{greeting}'),
        common_dlg_elements.RESET_POSTS_BUTTON,
        Back(Const(lexicon.BUTTONS['назад']), id="btn_back_ex"),
        getter=getter_post_utilities,
        state=states.SG_Main.post_utilities,
    ),
    Window(
        Format('{greeting}'),
        SwitchTo(Const(lexicon.BUTTONS['назад']), id="btn_back", state=states.SG_Main.start),
        getter=getter_scheme,
        state=states.SG_Main.scheme,
    ),
    Window(
        Format('{greeting}'),
        SwitchTo(Const(lexicon.BUTTONS['назад']), id="btn_back", state=states.SG_Main.start),
        getter=getter_reference,
        state=states.SG_Main.reference,
    ),
    Window(
        Format('{greeting}'),
        *common_dlg_elements.LANGS_BUTTONS,
        SwitchTo(Const(lexicon.BUTTONS['назад']), id="btn_back", state=states.SG_Main.for_viewing),
        getter=getter_language,
        state=states.SG_Main.language,
    ),
)

dialog_start_moderate = Dialog(*dialog_interface)