import asyncio
import logging
import concurrent.futures as pool
from time import sleep
from aiogram import Bot, Dispatcher, F, Router
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import CommandStart, ExceptionTypeFilter
from aiogram_dialog.api.exceptions import UnknownIntent, UnknownState, OutdatedIntent
from aiogram_dialog import setup_dialogs
from aiogram_dialog import DialogManager, StartMode
from datetime import datetime
#
import models.data_model

# routers
from routers.console import terminal
from routers.logers import app_loger
from routers.bots.bots import BotExt, current_bots
from routers.dispatcher import parsing_dispatcher

# models
from models.data_model import get_elements
from models.data.bot import Bot as BotModel






def init_bots():
    # Получаем список ботов из базы
    mbots = get_elements(BotModel)
    bots = []
    for mbot in mbots:
        # Настраиваем бота
        try:
            bot = BotExt(mbot.token, mbot.parse_mode, mbot.active)
            if type(bot) is BotExt:
                bots.append(bot)
            else:
                print(f'Создать объект бота {mbot.name} нее удалось. Ошибка: {bot}')
                app_loger.error(f'Создать объект бота {mbot.name} нее удалось. Ошибка: {bot}')
                continue
        except Exception as ex:
            print(f'Создать объект бота {mbot.name} нее удалось. Ошибка: {ex}')
            app_loger.error(f'Создать объект бота {mbot.name} нее удалось. Ошибка: {ex}')
            continue
    return bots

async def start_polling(bot: BotExt):
    # Запускаем прослушивание бота
    try:
        if bot.active == 1:
            await bot.dispatcher.start_polling(bot)
    except Exception as ex:
        print(f'Ошибка в работе бота смотрите логи!')
        app_loger.error(f'Ошибка в работе бота: {ex}')


async def main():

    #
    # logger.info('Starting bot')
    # storage: MemoryStorage = MemoryStorage()
    # try:
    #     bot: Bot = Bot(token=ProjectConfig.BOT_TOKEN, parse_mode='HTML')
    # except Exception as ex:
    #     print(f'Создать объект бота нее удалось: {ex}')
    #     return
    # try:
    #     # Получаем конфигурацияю проекта
    #     project_config = config.ProjectConfig()
    #     # Создаем парсер
    #     # target_ids=[-100157872], target_names=['lurkopub_alive']
    #     parser_params = ParseParams(target_ids=[-100157872, -26406986, -206243391], target_names=['lurkopub_alive', 'lurkopub', 'lurkupub'],
    #                                 token=project_config.VK_API_TOKEN, reserve_token=project_config.VK_API_TOKEN,
    #                                 min_text_len=project_config.PARSER_MIN_TEXT_LEN,
    #                                 telegraph_token=project_config.TELEGRAPH_TOKEN,
    #                                 telegraph_author=project_config.TELEGRAPH_AUTHOR,
    #                                 telegraph_author_url=project_config.TELEGRAPH_AUTHOR_URL,
    #                                 channel_id=project_config.CHANNEL_ID, errors_channel_id=project_config.CHANNEL_ID_ERROR_REPORT,
    #                                 proxy_http=project_config.PROXY_HTTP, proxy_https=project_config.PROXY_HTTPS,
    #                                 bot_url=project_config.BOT_URL)
    #     parser_obj = ParserApp(project_config, parser_params)
    #     # Запусп процесса автопубликации
    #     publicate_task = asyncio.create_task(publicator(parser_obj, bot))
    #     # Запусп процесса обновления
    #     updater_task = asyncio.create_task(content_update(parser_obj, bot))
    # Запуск консоли управления
    # console_task = asyncio.create_task(terminal.console({}))
    #     #
    #     dp: Dispatcher = Dispatcher(storage=storage)
    #     # Срздаем роутер для диалогов
    #     dialog_router = Router()
    #     # Регистрируем все диалоги
    #     dialog_router.include_routers(
    #         start_menu.dialog_start_menu,
    #         find_post.dialog_get_post,
    #         favourites.dialog_favourites,
    #         news.dialog_news,
    #         random_post.dialog_random_post,
    #         nothing.dialog_nothing,
    #         tops.dialog_tops,
    #         offer_post.dialog_offer_post,
    #     #     find_judge.dialog_find_judge,
    #     #     find_court.dialog_court_found_result,
    #     #     find_court.dialog_find_court,
    #     #     find_person.dialog_person_found_result,
    #     #     find_person.dialog_find_person,
    #     #     user_case.dialog_user_cases,
    #     )
    #     # Регистрируем обработчики ошибок
    #     dp.errors.register(on_unknown_intent, ExceptionTypeFilter(UnknownIntent), )
    #     dp.errors.register(on_unknown_state, ExceptionTypeFilter(UnknownState), )
    #     dp.errors.register(on_outdated_intent, ExceptionTypeFilter(OutdatedIntent), )
    #     # Регистрируем основные роутеры
    #     dp.include_router(base_handlers.router)
    #     dp.include_router(btn_handlers.router)
    #     # Регистрируем диалоги в диспетчере
    #     dp.include_router(dialog_router)
    #     # Регистрируем прочие роутеры
    #     dp.include_router(other_handlers.router)
    #     # Просто нужно делать, чтобы все работало
    #     setup_dialogs(dp)
    #     # Формируем меню команд бота
    #     await set_command_menu(bot, menues.COMMAND_MENU)
    #     #
    #     # Просто нужно делать, чтобы все работало
    #     # await bot.delete_webhook(drop_pending_updates=True)  # убрать в продакшене
    # except Exception as ex:
    #     print(f'Ошибка запуска бота: {ex}')
    #     return
    # try:
    #     await dp.start_polling(bot)
    # except Exception as ex:
    #     print(f'Ошибка в работе бота смотрите логи!')
    #     logger.error(ex)
    pass


# global


if __name__ == '__main__':
    try:
        # Создаем диспетчер парсеров

        # Создаем ботов
        current_bots = init_bots()
        # Запускаем вспомагательные задачи
        loop = asyncio.get_event_loop()
        tasks = [
            loop.create_task(terminal.console({}))
        ]
        # Запускаем боты
        for bot in current_bots:
            tasks.append(loop.create_task(start_polling(bot)))
        #
        loop.run_until_complete(asyncio.wait(tasks))
        loop.close()
        print('Приложение завершено.')
        #asyncio.run(main())
        pass
    except (KeyboardInterrupt, SystemExit):
        #logger.info('App stopped!')
        pass