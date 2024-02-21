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
from routers.parsing.rating import get_avg_views
from routers.bots.telegram.bots import start_bots
#from routers.bots.errors import BotErrors

from routers.bots.telegram.bots import init_bots, BotStatus

# models
from models.data.bot import Bot as BotModel
from models.data.post import Post, ModerateStates
from models.data.post_text_FTS import PostText
from models.data.photo import Photo
from models.data.audio import Audio
from models.data.audio_upload import AudioUpload
from models.data.video import Video
from models.data.docs import Doc
from models.data.poll import Poll
from models.data.link import Link
from models.data.post_hashtag import Post_Hashtag
from models.data_model import delete_post
#
# dialogs
#from views.telegram.dialogs.dlg_start import dialog_start_menu

#views
from views.telegram.interface_dispather import load_bot_interfaces


# test block
test_dict = {}
test_dict['Маш'] = 'Миш'
test_dict['Вова'] = 'Петя'
text = 'Привет Маша. Как у Маши дела? Там идет Вова. Да это Вова.'
#


# end test block



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

async def service_task():
    # Задача сервиса
    # Удаляет посты помеченные к удалению
    while True:
        await asyncio.sleep(100000)
        try:
            num = 0
            posts_to_del = Post.select().where(Post.moderate == ModerateStates.ToDelete.value)
            for post in posts_to_del:
                num += 1
                delete_post(post=post)
        except Exception as ex:
            pass
        await asyncio.sleep(100000)


async def amain():
    #
    tasks = []
    tasks.append(task_void())
    tasks.append(service_task())
    #
    #t_task = asyncio.create_task(test_task(), name='Test')
    # Запускаем ботов
    await start_bots()
    # Запускаем задачи парсинга
    await parsers_dispatcher.init_tasks()
    # Запускаем публикаторы
    await publicators_unit.init_current_publicators()
    # Создаем задачу терминала
    # tasks.append(terminal.console({}))
    con_task = asyncio.create_task(terminal.console({}), name='Terminal')
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