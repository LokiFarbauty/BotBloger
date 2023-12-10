import asyncio

from aiogram import Bot, Dispatcher, F, Router
from aiogram_dialog.api.exceptions import UnknownIntent, UnknownState, OutdatedIntent
from aiogram_dialog import setup_dialogs
from aiogram.filters import ExceptionTypeFilter, CommandStart, Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram_dialog import DialogManager, StartMode

# routers
from routers.bots.errors import BotErrors
from routers.bots.exceptions import on_unknown_state, on_outdated_intent
from routers.bots.loger import bots_loger
from routers.bots.bots_utills import get_tg_user_names
from routers.bots.telegram.states import SG_enter_token_menu as start_dialog

# models
from models.data.user_bot import User_Bot
from models.data.user_bot import Bot as BotModel

current_bots = []



class BotExt(Bot):
    def __init__(self, token: str, parse_mode: str, active: int, public: int, *routers: Router):
        self.name = ''
        self.url = ''
        self.tg_id = 0
        self.active = active
        self.public = public
        self.storage: MemoryStorage = MemoryStorage()
        self.status = BotErrors.NoError
        self.polling_process = None
        try:
            self.bot = super().__init__(token=token, parse_mode=parse_mode)
            #self.bot = super(BotExt, self).__init__(token=token, parse_mode=parse_mode)
            #self.bot = Bot(token=token, parse_mode=parse_mode)
        except Exception as ex:
            bots_loger.error(f'Не удалось подключить бот {token}: Ошибка: {ex}')
            self.status = BotErrors.MainBotCreateError
            return
        dp: Dispatcher = Dispatcher(storage=self.storage)
        # Создаем роутер для диалогов
        self.dialog_router = Router()
        # Регистрируем все диалоги
        if len(routers) > 0:
            self.dialog_router.include_routers(*routers)
        dp.errors.register(self.on_unknown_intent, ExceptionTypeFilter(UnknownIntent), )
        dp.errors.register(on_unknown_state, ExceptionTypeFilter(UnknownState), )
        dp.errors.register(on_outdated_intent, ExceptionTypeFilter(OutdatedIntent), )
        # Регистрируем основные роутеры
        self.base_router: Router = Router()
        dp.include_router(self.base_router)
        self.btn_router: Router = Router()
        dp.include_router(self.btn_router)
        # Регистрируем диалоги в диспетчере
        dp.include_router(self.dialog_router)
        # Регистрируем прочие роутеры
        self.other_router: Router = Router()
        dp.include_router(self.other_router)
        #
        setup_dialogs(dp)
        # Формируем меню команд бота
        #await set_command_menu(bot, menues.COMMAND_MENU)
        self.dispatcher = dp

        @self.base_router.message(CommandStart())
        async def proc_start_command(message: Message, bot: Bot, dialog_manager: DialogManager):
            # Проверяем зарегистрирован ли пользователь
            try:
                #await message.answer('Доступен', reply_markup=ReplyKeyboardRemove())
                user_id = message.from_user.id
                username, firstname, lastname = get_tg_user_names(message.from_user)
                # Получаем бота из базы
                bot_obj = BotModel.get_obj(bot.token)
                if type(bot_obj) is not BotModel:
                    bots_loger.critical(f'Не удалось обновить информацию о боте: {bot.token}')
                # Проверяем пользователя
                user = User_Bot.check_user(bot_obj, user_id, username, firstname, lastname)
                #print(await bot.get_my_name())
                # Закрываем все ранее открытые диалоги
                try:
                    # await dialog_manager.done()
                    await dialog_manager.reset_stack()
                except:
                    pass
                #
                try:
                    bot_info = await bot.get_me()
                    bot_url = bot_info.username
                    bot_name = bot_info.full_name
                    bot_obj = bot_obj.refresh_bot_info(name=bot_name, url=bot_url, tg_id=bot_info.id)
                except Exception as ex:
                    pass
                # Выводим стартовое меню
                await dialog_manager.start(start_dialog.start, mode=StartMode.RESET_STACK, data={'user': user})

            except Exception as ex:
                bots_loger.error(f"CommandStart(): {ex}")

        @self.base_router.message(Command('back'))
        async def proc_back_command(message: Message, bot: Bot, dialog_manager: DialogManager):
            # Проверяем зарегистрирован ли пользователь
            try:
                # Проверяем зарегистрирован ли пользователь
                user_id = message.from_user.id
                username, firstname, lastname = get_tg_user_names(message.from_user)
                user = User_Bot.check_user(bot.token, user_id, username, firstname, lastname)
                await dialog_manager.done()
            except Exception as ex:
                bots_loger.error(f"Command('back'): {ex}")

        @self.other_router.message(F.text)
        async def proc_other_mess(message: Message, bot: Bot, dialog_manager: DialogManager):
            try:
                # Проверяем зарегистрирован ли пользователь
                user_id = message.from_user.id
                username, firstname, lastname = get_tg_user_names(message.from_user)
                user = User_Bot.check_user(bot.token, user_id, username, firstname, lastname)
                # Выводим диалог
                await dialog_manager.start(SG_start_menu.start, mode=StartMode.RESET_STACK, data={'user': user})
            except Exception as ex:
                bots_loger.error(f"F.text: {ex}")

    async def on_unknown_intent(self, event, dialog_manager: DialogManager):
        """Example of handling UnknownIntent Error and starting new dialog."""
        # logger.error(f'Сработало исключение: неизвестный замысел: {event.exception}!')
        # await dialog_manager.start(DialogSG.greeting, mode=StartMode.RESET_STACK, show_mode=ShowMode.SEND,)
        pass

    async def start_polling(self):
        # Запускаем прослушивание бота
        try:
            self.status = BotErrors.InWork
            await self.dispatcher.start_polling(self)
        except Exception as ex:
            self.status = BotErrors.Broken
            print(f'Ошибка в работе бота {self.name} смотрите логи!')
            bots_loger.error(f'Ошибка в работе бота {self.name}: {ex}')

    async def start_polling_task(self):
        # Запускаем прослушивание бота
        try:
            self.status = BotErrors.InWork
            self.polling_process = asyncio.create_task(self.start_polling(), name=self.name)
            #await self.dispatcher.start_polling(self)
        except Exception as ex:
            self.status = BotErrors.Broken
            print(f'Ошибка в работе бота {self.name} смотрите логи!')
            bots_loger.error(f'Ошибка в работе бота {self.name}: {ex}')

    async def stop_polling(self):
        # Останавливает прослушивание бота
        try:
            self.status = BotErrors.Stopped
            await self.dispatcher.stop_polling()
        except Exception as ex:
            self.status = BotErrors.Broken
            print(f'Ошибка в работе бота {self.name} смотрите логи!')
            bots_loger.error(f'Ошибка в работе бота {self.name}: {ex}')
        return self.status.value

