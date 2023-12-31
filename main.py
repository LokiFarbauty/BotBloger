import asyncio

# не удалять
import routers.parsing.dispatcher as dispatcher
#

# routers
from routers.console import terminal
from routers.logers import app_loger
from routers.bots.telegram.bots import BotExt
import routers.bots.telegram.bots as bots_unit
from routers.bots.errors import BotErrors
from routers.bots.telegram.bots import init_bots

# models
from models.data.bot import Bot as BotModel

#


# dialogs
#from views.telegram.dialogs.dlg_start import dialog_start_menu






# async def start_polling(bot: BotExt):
#     # Запускаем прослушивание бота
#     try:
#         if bot.active == 1:
#             await bot.dispatcher.start_polling(bot)
#     except Exception as ex:
#         print(f'Ошибка в работе бота смотрите логи!')
#         app_loger.error(f'Ошибка в работе бота: {ex}')


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
async def task_void():
    # блокировка на некоторое время
    while True:
        await asyncio.sleep(0.0001)

async def test_task():
    # блокировка на некоторое время
    i = 0
    while True:
        i += 1
        print(i)
        await asyncio.sleep(1)

async def amain():
    #
    tasks = []
    tasks.append(task_void())
    # Создаем задачу терминала
    # tasks.append(terminal.console({}))
    con_task = asyncio.create_task(terminal.console({}), name='Terminal')
    #
    #t_task = asyncio.create_task(test_task(), name='Test')
    # Создаем ботов
    cr_bots = await init_bots()
    # Запускаем задачи
    await dispatcher.init_tasks()
    bots_unit.current_bots = cr_bots
    for i, bot in enumerate(bots_unit.current_bots, 0):
        #tasks.append(start_polling(bot))
        if bot.active == 1:
            #tasks.append(bot.start_polling())
            try:
                bots_unit.current_bots[i].polling_process = asyncio.create_task(bot.start_polling(), name=bot.name)
                bots_unit.current_bots[i].status = BotErrors.InWork
            except Exception as ex:
                bots_unit.current_bots[i].status = BotErrors.Broken
                print(f'Запустить бота {bot.name} не удалось. Ошибка: {ex}')
                app_loger.warning(f'Запустить бота {bot.name} не удалось. Ошибка: {ex}')
        else:
            bots_unit.current_bots[i].status = BotErrors.Stopped
    #
    # Запускаем бесконечные задачи
    await asyncio.gather(*tasks)

if __name__ == '__main__':
    try:
        # Создаем диспетчер парсеров
        # Создаем ботов
        # current_bots = init_bots()
        # Запускаем вспомагательные задачи
        # Вариант 1
        # loop = asyncio.get_event_loop()
        # tasks = [
        #     loop.create_task(terminal.console({}))
        # ]
        # # Запускаем боты
        # for bot in current_bots:
        #     tasks.append(loop.create_task(start_polling(bot)))
        # #
        # loop.run_until_complete(asyncio.wait(tasks))
        # loop.close()
        # Вариант 2
        asyncio.run(amain())
        print('Приложение завершено.')
        pass
    except (KeyboardInterrupt, SystemExit):
        #logger.info('App stopped!')
        pass