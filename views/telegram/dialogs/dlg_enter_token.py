from aiogram.types import CallbackQuery, ContentType, Message, FSInputFile, ReplyKeyboardRemove
from aiogram import Bot, Dispatcher, F, Router
from aiogram_dialog import (
    ChatEvent, Dialog, DialogManager, setup_dialogs,
    ShowMode, StartMode, Window,
)
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Cancel, Button, Row, Select, SwitchTo, Start, Next
from aiogram_dialog.widgets.text import Const, Format, Multi, ScrollingText
from routers.bots.lexicon import *
from routers.parsing.interface_parser import ParseParams
from routers.dispatcher import parsing_dispatcher
from routers.bots.loger import bots_loger
from routers.bots.states import SG_enter_token_menu


async def start_main_menu(**_kwargs):
    #dm = _kwargs['dialog_manager']
    #args[1].dialog_data = data
    pass

async def getter_start_menu(**_kwargs):
    dm = _kwargs['dialog_manager']
    try:
        user = dm.start_data['user']
        user_name = f'{user.firstname} {user.lastname}'
    except:
        user_name = ''
    return {
        "greeting": GREETINGS['старт'].format(user_name),
        }

async def words_handler(message: Message, message_input: MessageInput,
                       dialog_manager: DialogManager):
    '''
    Обработчик ввода слов для поиска
    :param message:
    :param message_input:
    :param dialog_manager:
    :return:
    '''
    try:
        # Вычленяем нужную информацию из ссылки
        ac_url=message.text
        # получаем токен
        t_pos = ac_url.find('access_token=')
        if t_pos == -1:
            await message.answer(GREETINGS['нет токена'])
            return
        end_t_pos = ac_url.find('&', t_pos)
        access_token = ac_url[t_pos+len('access_token='):end_t_pos]
        # получаем пользователя
        t_pos = ac_url.find('user_id=')
        if t_pos == -1:
            await message.answer(GREETINGS['нет токена'])
            return
        end_t_pos = ac_url.find('&', t_pos)
        vk_user_id = ac_url[t_pos + len('user_id='):end_t_pos]
        # Тестируем токен
        params = ParseParams(target_id=1, token=access_token, post_count=10, use_free_proxy=False)
        parser = parsing_dispatcher.get_parser('ВКонтакте')
        if parser != None:
            parse_res = await parser.parse(params)
            dialog_manager.dialog_data['vk_user_id'] = vk_user_id
            dialog_manager.dialog_data['access_token'] = access_token
            # end = time.time()
            # print(f'\nВремя операции - {end - start} сек.')
            await dialog_manager.next()
        else:
            bots_loger.error(f'Ошибка words_handler: не найден парсер ВКонтакте')
            await message.answer(GREETINGS['ошибка'])
    except Exception as ex:
        bots_loger.error(f'Ошибка words_handler: {ex}')
        await message.answer(GREETINGS['ошибка'])
        pass

    #await dialog_manager.start(states.SG_find_post.show_result, mode=StartMode.RESET_STACK, data={'cases': cases})
    # Завершаем диалог
    #await dialog_manager.done()

dialog_start_menu = Dialog(
    Window(
        Format('{greeting}'),
        MessageInput(words_handler, content_types=[ContentType.TEXT]),
        # Row(
        #     Start(Const(START_BUTTONS['новое']), id="dlg_news", state=states.SG_news.start),
        #     Start(Const(START_BUTTONS['найти']), id="dlg_find", state=states.SG_find_post.input_words),
        # ),
        # Row(
        #     Start(Const(START_BUTTONS['топ']), id="dlg_top", state=states.SG_tops.start),
        #     Start(Const(START_BUTTONS['случайно']), id="dlg_random", state=states.SG_random.start),
        # ),
        # Row(
        #     Start(Const(START_BUTTONS['избранное']), id="dlg_favour", state=states.SG_favourites.start),
        #     Start(Const(START_BUTTONS['предложить']), id="dlg_offer", state=states.SG_offer_post.add_text),
        # ),
        state=SG_enter_token_menu.enter_token,
    ),
    getter=getter_start_menu,
)