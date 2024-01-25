import asyncio
import logging

# не удалять
from routers.parsing.parsers_dispatсher import parsers_dispatcher
import routers.publicate.publicators as publicators_unit
import views.telegram.interface_dispather # Загрузка интерфейсов ботов
#

# routers
from routers.console import terminal
from routers.logers import app_loger
from routers.bots.telegram.bots import BotExt
from routers.bots.telegram.bots import start_bots
#from routers.bots.errors import BotErrors

from routers.bots.telegram.bots import init_bots, BotStatus

# models
from models.data.bot import Bot as BotModel

#
# dialogs
#from views.telegram.dialogs.dlg_start import dialog_start_menu

#views
from views.telegram.interface_dispather import load_bot_interfaces




async def main():
    pass


# global
async def task_void():
    # блокировка на некоторое время
    while True:
        await asyncio.sleep(0.01)

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
    #
    # Создаем задачу терминала
    # tasks.append(terminal.console({}))
    con_task = asyncio.create_task(terminal.console({}), name='Terminal')
    #
    #t_task = asyncio.create_task(test_task(), name='Test')
    # Запускаем ботов
    await start_bots()
    # Запускаем задачи парсинга
    await parsers_dispatcher.init_tasks()
    # Запускаем публикаторы
    await publicators_unit.init_current_publicators()
    # Запускаем бесконечные задачи
    await asyncio.gather(*tasks)

if __name__ == '__main__':
    try:
        logging.basicConfig(level=logging.CRITICAL)
        asyncio.run(amain())
        print('Приложение завершено.')
        pass
    except (KeyboardInterrupt, SystemExit):
        #logger.info('App stopped!')
        pass