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
import os

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
from views.telegram.interface_dispather import get_bot_interface
#from views.telegram.tmp.dialogs_dispatcher import bot_dialogs
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
    def __init__(self, token: str, parse_mode: str, active: int, public: int, dispatcher: Dispatcher):
        self.name = ''
        self.url = ''
        self.tg_id = 0
        self.active = active  # флаг автозапуска
        self.public = public # 0 - бот частный, 1 - публичный
        self.status = BotStatus.NoError # текущий статус бота
        self.polling_process = None # процесс пулинга
        try:
            self.bot = super().__init__(token=token, parse_mode=parse_mode) # готовим базовый бот
            #self.bot = super(BotExt, self).__init__(token=token, parse_mode=parse_mode)
            #self.bot = Bot(token=token, parse_mode=parse_mode)
        except Exception as ex:
            bots_loger.error(f'Не удалось подключить бот {token}: Ошибка: {ex}')
            self.status = BotStatus.MainBotCreateError
            return
        self.dispatcher = dispatcher
        setup_dialogs(self.dispatcher)

    async def send_media_group_ex(self, **kwargs):
        # Отправка медиагруппы с проверкой общего размера файлов (больше 50 Мб не отправляет, приходится отправлять по частям)
        medias = kwargs['media']
        media_groups = []
        media_group = []
        group_file_size = 0
        index=0
        last_index = 0
        # Вычисляем общий размер файлов медиагруппы
        for media in medias:
            file_name = media.media.path
            filesize = os.path.getsize(file_name)
            group_file_size = group_file_size + filesize
            if group_file_size < 50000000:
                media_group.append(media)
            else:
                group_file_size = 0
                media_groups.append(media_group)
                media_group = []
                media_group.append(media)
        if len(media_group)>0:
            media_groups.append(media_group)
        for mg in media_groups:
            kwargs['media'] = mg
            answer = await self.send_media_group(**kwargs)
        pass

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
            Bot_interface = get_bot_interface(mbot.interface)
            #bot_dialogs = bot_interface.dialogs
            #bot = BotExt(mbot.token, mbot.parse_mode, mbot.active, mbot.public, 'None', *bot_dialogs)
            bot_interface = Bot_interface()
            bot = BotExt(mbot.token, mbot.parse_mode, mbot.active, mbot.public, bot_interface.dp)
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
    print(f'Загружено {len(bots)} ботов.')
    app_loger.info(f'Загружено {len(bots)} ботов.')
    #print(f'Запущено {len(bots)} ботов.')
    return bots

async def start_bots():
    # Запускаем боты
    cr_bots = await init_bots()
    print(f'Запуск ботов...')
    app_loger.info(f'Запуск ботов...')
    current_bots.extend(cr_bots)
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
