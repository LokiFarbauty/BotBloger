'''Модуль при импорте автоматически подгружает и привязывает к боту все диалоги изпапки dialogs'''

'''Модуль при импорте автоматически подгружает и привязывает к боту все диалоги изпапки dialogs'''

import os
import importlib
import inspect
from aiogram_dialog import DialogManager, StartMode
from aiogram_dialog import Dialog
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import Bot, Dispatcher, F, Router
from aiogram_dialog.api.exceptions import UnknownIntent, UnknownState, OutdatedIntent
from aiogram.filters import ExceptionTypeFilter, CommandStart, Command
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message
#
from models.data.user_bot import User_Bot
from models.data.bot import Bot as BotModel, BotStates
#
from routers.logers import bots_loger
from routers.bots.bots_utills import get_tg_user_names
#
from views.telegram.interface_pattern import BotViewInterface
# Диалоги
#from views.telegram.vk_sync.dialogs.start_dialog import SG_VKSync

#dlg_path = MAIN_PATH
dlg_path = os.path.dirname(os.path.abspath(__file__))+'\\dialogs\\' # путь к файлам диалогов
py_dlg_path = 'views.telegram.vk_sync.dialogs'


def get_dialogs_interfaces(interface_name='dialog_interface',path=dlg_path, py_path=py_dlg_path):
    # Подгружаем все найденые диалоги
    dialogs_lst = []
    # проверяем директорию
    if not os.path.isdir(path):
        bots_loger.critical(
            f'Невозможно получить диалоги для ботов: отсутствует директория {path}')
        bots_loger.info(f'Создание диалогов прервано.')
        return dialogs_lst
    # Получаем список файлов в папке диалогов
    dialog_files = os.listdir(path)
    # Пробуем подключить парсеры
    for dlg_file in dialog_files:
        try:
            pos = dlg_file.find('.py')
            if pos == -1:
                continue
            else:
                dlg_file = dlg_file[:pos]
            #
            command_module = importlib.import_module(f'{py_path}.{dlg_file}')
            members = inspect.getmembers(command_module)
            for name, obj in members:
                if name == interface_name:
                    dialogs_lst.append(obj)
        except Exception as ex:
            bots_loger.error(f'Ошибка загрузки диалога {dlg_file}: {ex}')
    return dialogs_lst


class VKSyncView(BotViewInterface):
    name = 'VKSync'
    def __init__(self):
        self.description = 'Интерфейс бота синхронизации ВКонтакте и Телеграм.'
        self.file = os.path.abspath(__file__)
        self.dialogs = []
        self.dialogs_interfaces = get_dialogs_interfaces()
        for di in self.dialogs_interfaces:
            dialog = Dialog(*di)
            self.dialogs.append(dialog)
        self.storage: MemoryStorage = MemoryStorage()  # Это нужно для диалогов
        self.dp: Dispatcher = Dispatcher(storage=self.storage)
        self.dialog_router = Router()
        if len(self.dialogs) > 0:
            self.dialog_router.include_routers(*self.dialogs)
        self.dp.include_router(self.dialog_router)
        self.dp.errors.register(self.on_unknown_intent, ExceptionTypeFilter(UnknownIntent), )
        self.dp.errors.register(self.on_unknown_state, ExceptionTypeFilter(UnknownState), )
        self.dp.errors.register(self.on_outdated_intent, ExceptionTypeFilter(OutdatedIntent), )
        self.dp.message.register(self.proc_start_command, CommandStart())
        self.dp.message.register(self.proc_back_command, Command('back'))
        #self.dp.message.register(self.proc_other_mess, F.text)

    async def proc_start_command(self, message: Message, bot: Bot, dialog_manager: DialogManager):
        try:
            # Проверяем зарегистрирован ли пользователь
            user_id = message.from_user.id
            username, firstname, lastname = get_tg_user_names(message.from_user)
            # Получаем бота из базы
            bot_obj = BotModel.get_obj(bot.token)
            if type(bot_obj) is not BotModel:
                bots_loger.critical(f'Бот: {bot.token} в базе не найден.')
                return
            # Проверяем пользователя
            user = User_Bot.check_user(bot_obj, user_id, username, firstname, lastname)
            # print(await bot.get_my_name())
            # Закрываем все ранее открытые диалоги
            try:
                # await dialog_manager.done()
                await dialog_manager.reset_stack()
            except:
                pass
            # Обновляем информацию о боте
            try:
                bot_info = await bot.get_me()
                bot_obj = bot_obj.refresh_bot_info(name=bot_info.first_name, url=bot_info.username, tg_id=bot_info.id,
                                                   state=BotStates.InWork.value)
            except Exception as ex:
                bots_loger(f'Не удалось обновить информацию о боте: {bot_obj.get_id()}. Ошибка: {ex}')
            await dialog_manager.start(SG_VKSync.start, mode=StartMode.RESET_STACK, data={'user': user})
        except Exception as ex:
            try:
                bots_loger.error(f"Ошибка CommandStart() в боте {bot_obj.get_id()}: {ex}")
            except:
                pass

    async def proc_back_command(self, message: Message, bot: Bot, dialog_manager: DialogManager):
        # Проверяем зарегистрирован ли пользователь
        try:
            await dialog_manager.back()
        except Exception as ex:
            bots_loger.error(f"Command('back'): {ex}")


    async def proc_other_mess(self, message: Message, bot: Bot, dialog_manager: DialogManager):
        try:
            pass
        except Exception as ex:
            bots_loger.error(f"F.text: {ex}")

    async def on_unknown_intent(self, event, dialog_manager: DialogManager):
        """Example of handling UnknownIntent Error and starting new dialog."""
        if event.update.callback_query:
            try:
                await event.update.callback_query.answer("Бот обновился. Пожалуйста перейдите в главное меню.")
                try:
                    await event.update.callback_query.message.delete()
                except TelegramBadRequest:
                    pass  # whatever
            except:
                pass
        try:
            user = dialog_manager.middleware_data['event_from_user']
            bot = dialog_manager.middleware_data['bot']
            await bot.send_message(user.id, 'Бот обновился. Пожалуйста нажмите /start')
        except:
            pass

    async def on_unknown_state(self, event, dialog_manager: DialogManager):
        """Example of handling UnknownState Error and starting new dialog."""
        try:
            user = dialog_manager.middleware_data['event_from_user']
            bot = dialog_manager.middleware_data['bot']
            await bot.send_message(user.id, 'Бот обновился. Пожалуйста нажмите /start')
        except:
            pass

    async def on_outdated_intent(self, event, dialog_manager: DialogManager):
        """Example of handling UnknownState Error and starting new dialog."""
        try:
            user = dialog_manager.middleware_data['event_from_user']
            bot = dialog_manager.middleware_data['bot']
            await bot.send_message(user.id, 'Бот обновился. Пожалуйста нажмите /start')
            await dialog_manager.reset_stack()
        except:
            pass



