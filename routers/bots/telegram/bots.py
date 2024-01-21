'''Модуль отвечает за телеграмм-ботов.
В модуле определяется рассширеный клас бота BotExt, создаются aiogram-роутеры.
Также модуль содержит функции инициализации и запуска ботов.
current_bots - список текущих ботов'''

import asyncio

from aiogram import Bot, Dispatcher, F, Router
from aiogram_dialog.api.exceptions import UnknownIntent, UnknownState, OutdatedIntent
from aiogram_dialog import setup_dialogs
from aiogram.filters import ExceptionTypeFilter, CommandStart, Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message
from aiogram_dialog import DialogManager, StartMode
from aiogram.exceptions import TelegramBadRequest
import enum

# routers
from routers.logers import bots_loger, app_loger
from routers.bots.bots_utills import get_tg_user_names

# models
from models.data.user_bot import User_Bot
from models.data.bot import Bot as BotModel, BotStates
from models.data.parser import Parser
from models.data.user import User
from models.data_model import get_elements

# views
#from views.telegram.tmp.dialogs_dispatcher import bot_dialogs
from views.telegram.interface_dispather import get_bot_interface
#from views.telegram.none_interface.dialogs_dispatcher import BotView

# удалить



current_bots = []

class BotStatus(enum.Enum):
    NoError = 'ошибок нет, не запущен'
    MainBotCreateError = 'ошибка создания бота'
    InWork = 'работает'
    Stopped = 'остановлен'
    Broken = 'сломался'

class BotExt(Bot):
    def __init__(self, token: str, parse_mode: str, active: int, public: int, interface_name: str, *routers: Router):
        self.name = ''
        self.url = ''
        self.tg_id = 0
        self.active = active  # флаг автозапуска
        self.public = public # 0 - бот частный, 1 - публичный
        self.storage: MemoryStorage = MemoryStorage() # Это нужно для диалогов
        self.status = BotStatus.NoError # текущий статус бота
        self.polling_process = None # процесс пулинга
        tt_pos = token.find(':')
        self.router_name = token[:tt_pos]
        try:
            self.bot = super().__init__(token=token, parse_mode=parse_mode) # готовим базовый бот
            #self.bot = super(BotExt, self).__init__(token=token, parse_mode=parse_mode)
            #self.bot = Bot(token=token, parse_mode=parse_mode)
        except Exception as ex:
            bots_loger.error(f'Не удалось подключить бот {token}: Ошибка: {ex}')
            self.status = BotStatus.MainBotCreateError
            return
        dp: Dispatcher = Dispatcher(storage=self.storage)
        # Создаем роутер для диалогов
        self.dialog_router = Router(name=self.router_name)
        # Регистрируем все диалоги
        if len(routers) > 0:
            self.dialog_router.include_routers(*routers)
        dp.errors.register(on_unknown_intent, ExceptionTypeFilter(UnknownIntent), )
        dp.errors.register(on_unknown_state, ExceptionTypeFilter(UnknownState), )
        dp.errors.register(on_outdated_intent, ExceptionTypeFilter(OutdatedIntent), )
        # dp.errors.register(on_telegram_error)
        # , ExceptionTypeFilter(TelegramServerError),
        #                            ExceptionTypeFilter(TelegramRetryAfter),
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

        # @self.base_router.error(ExceptionTypeFilter(TelegramNetworkError), F.update.message.as_("message"))
        # async def handle_my_custom_exception(event: ErrorEvent, message: Message):
        #     # do something with error
        #     print("Oops, something went wrong!")


        @self.base_router.message(CommandStart())
        async def proc_start_command(message: Message, bot: Bot, dialog_manager: DialogManager):
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
                #print(await bot.get_my_name())
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
                # Переадресовываем пользователя на точку входа интерфейса
                #await dialog_manager.start(SG_bot_config.show_menu, mode=StartMode.RESET_STACK, data={'user': user})
                # получаем интерфейс бота
                if bot_obj.interface == None:
                    bot_obj.interface = 'None'
                bot_interface = get_bot_interface(bot_obj.interface)
                if bot_interface != None:
                    await dialog_manager.start(bot_interface.start_dialog.start, mode=StartMode.RESET_STACK, data={'user': user})
            except Exception as ex:
                try:
                    bots_loger.error(f"Ошибка CommandStart() в боте {bot_obj.get_id()}: {ex}")
                except:
                    pass

        @self.base_router.message(Command('back'))
        async def proc_back_command(message: Message, bot: Bot, dialog_manager: DialogManager):
            # Проверяем зарегистрирован ли пользователь
            try:
                # # Проверяем зарегистрирован ли пользователь
                # user_id = message.from_user.id
                # username, firstname, lastname = get_tg_user_names(message.from_user)
                # # Получаем бота из базы
                # bot_obj = BotModel.get_obj(bot.token)
                # if type(bot_obj) is not BotModel:
                #     bots_loger.critical(f'Не удалось обновить информацию о боте: {bot.token}')
                # # Проверяем наличие связи пользователя с ботом
                # user = User_Bot.check_user(bot_obj, user_id, username, firstname, lastname)
                await dialog_manager.back()
            except Exception as ex:
                bots_loger.error(f"Command('back'): {ex}")

        @self.other_router.message(F.text)
        async def proc_other_mess(message: Message, bot: Bot, dialog_manager: DialogManager):
            try:
                pass
                # # Проверяем зарегистрирован ли пользователь
                # user_id = message.from_user.id
                # username, firstname, lastname = get_tg_user_names(message.from_user)
                # user = User_Bot.check_user(bot.token, user_id, username, firstname, lastname)
                # # Выводим диалог
                # await dialog_manager.start(start_dialog.start, mode=StartMode.RESET_STACK, data={'user': user})
            except Exception as ex:
                bots_loger.error(f"F.text: {ex}")


    async def start_polling(self):
        # Запускаем прослушивание бота (так бота лучше не запускать используй start_polling_task)
        try:
            self.status = BotStatus.InWork
            await self.dispatcher.start_polling(self)
        except Exception as ex:
            self.status = BotStatus.Broken
            print(f'Ошибка в работе бота {self.name} смотрите логи!')
            bots_loger.error(f'Ошибка в работе бота {self.name}: {ex}')

    async def start_polling_task(self):
        # Запускаем прослушивание бота в качестве отдельной задачи
        try:
            self.status = BotStatus.InWork
            self.polling_process = asyncio.create_task(self.start_polling(), name=self.name)
            #await self.dispatcher.start_polling(self)
        except Exception as ex:
            self.status = BotStatus.Broken
            print(f'Ошибка в работе бота {self.name} смотрите логи!')
            bots_loger.error(f'Ошибка в работе бота {self.name}: {ex}')

    async def stop_polling(self):
        # Останавливает прослушивание бота
        try:
            self.status = BotStatus.Stopped
            await self.dispatcher.stop_polling()
        except Exception as ex:
            self.status = BotStatus.Broken
            print(f'Ошибка в работе бота {self.name} смотрите логи!')
            bots_loger.error(f'Ошибка в работе бота {self.name}: {ex}')
        return self.status.value

async def on_unknown_intent(event, dialog_manager: DialogManager):
    """Example of handling UnknownIntent Error and starting new dialog."""
    # logger.error(f'Сработало исключение: неизвестный замысел: {event.exception}!')
    # await dialog_manager.start(DialogSG.greeting, mode=StartMode.RESET_STACK, show_mode=ShowMode.SEND,)
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

async def on_unknown_state(event, dialog_manager: DialogManager):
    """Example of handling UnknownState Error and starting new dialog."""
    # logging.error("Restarting dialog: %s", event.exception)
    # logger.error(f'Сработало исключение: неизвестное состояние: {event.exception}!')
    # print('Error: on_unknown_state')
    # await dialog_manager.start(DialogSG.greeting, mode=StartMode.RESET_STACK, show_mode=ShowMode.SEND,)
    try:
        user = dialog_manager.middleware_data['event_from_user']
        bot = dialog_manager.middleware_data['bot']
        await bot.send_message(user.id, 'Бот обновился. Пожалуйста нажмите /start')
    except:
        pass

async def on_outdated_intent(event, dialog_manager: DialogManager):
    """Example of handling UnknownState Error and starting new dialog."""
    try:
        # await dialog_manager.done()
        user = dialog_manager.middleware_data['event_from_user']
        bot = dialog_manager.middleware_data['bot']
        await bot.send_message(user.id, 'Бот обновился. Пожалуйста нажмите /start')
        await dialog_manager.reset_stack()
        # logger.error(f'Сработало исключение: on_outdated_intent: {event.exception}!')
    except:
        pass
    # await dialog_manager.start(states.SG_start_menu.start, mode=StartMode.RESET_STACK)

async def get_BotExt(bot_mld: BotModel)-> BotExt:
    # Возвращает объект бота по его модели
    bot_pr = None
    for bot in current_bots:
        if bot.name == bot_mld.name:
            return bot
    return bot_pr


async def init_bots():
    # Получаем список ботов из базы
    print(f'Загрузка ботов...')
    app_loger.info(f'Загрузка ботов...')
    mbots = get_elements(BotModel)
    bots = []
    bots_names = []
    for mbot in mbots:
        # Настраиваем бота
        try:
            # Получаем интерфейс
            if mbot.interface == None:
                mbot.interface = 'None'
            bot_interface = get_bot_interface(mbot.interface)
            bot_dialogs = bot_interface.dialogs
            bot = BotExt(mbot.token, mbot.parse_mode, mbot.active, mbot.public, 'None', *bot_dialogs)
            # проверяем работоспособность ботов
            try:
                bot_info = await bot.get_me()
                # обновляем информацию о боте
                #mbot.refresh_bot_info(bot_info.first_name, bot_info.username, bot_info.id)
                mbot.refresh_bot_info(name=bot_info.first_name, url=bot_info.username, tg_id=bot_info.id,
                                         state=BotStates.InWork.value)
                bot.name = bot_info.first_name
                bot.url = bot_info.username
                bot.tg_id = bot_info.id
                #print(f'Бот {bot.name} загружен.')
                app_loger.info(f'Бот <{bot.name}> загружен.')
            except Exception as ex:
                app_loger.warning(f'Установить связь с ботом {mbot.name} не удалось. Ошибка: {ex}')
                continue
            if type(bot) is BotExt:
                bots.append(bot)
            else:
                print(f'Создать объект бота {mbot.name} нее удалось. Ошибка: не правильный тип бота')
                app_loger.error(f'Создать объект бота {mbot.name} нее удалось. не правильный тип бота')
                continue
            bots_names.append(bot.name)
        except Exception as ex:
            print(f'Создать объект бота {mbot.name} нее удалось. Ошибка: {ex}')
            app_loger.error(f'Создать объект бота {mbot.name} нее удалось. Ошибка: {ex}')
            continue
    app_loger.info(f'Загружено {len(bots)} ботов.')
    #print(f'Запущено {len(bots)} ботов.')
    return bots

async def start_bots():
    # Запускаем боты
    cr_bots = await init_bots()
    print(f'Запуск ботов...')
    app_loger.info(f'Запуск ботов...')
    current_bots = cr_bots
    bot_num = 0
    for i, bot in enumerate(current_bots, 0):
        #tasks.append(start_polling(bot))
        if bot.active == 1:
            #tasks.append(bot.start_polling())
            try:
                current_bots[i].polling_process = asyncio.create_task(bot.start_polling(), name=bot.name)
                print(f'Бот <{current_bots[i].name}> запущен.')
                app_loger.info(f'Бот <{current_bots[i].name}> запущен.')
                current_bots[i].status = BotStatus.InWork
                bot_num +=1
            except Exception as ex:
                current_bots[i].status = BotStatus.Broken
                #print(f'Запустить бота {bot.name} не удалось. Ошибка: {ex}')
                app_loger.warning(f'Запустить бота {bot.name} не удалось. Ошибка: {ex}')
        else:
            current_bots[i].status = BotStatus.Stopped
    print(f'Запущено {bot_num} ботов.')
    app_loger.info(f'Запущено {bot_num} ботов.')
