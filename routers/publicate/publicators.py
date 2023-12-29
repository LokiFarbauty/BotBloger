'''Модуль отвечает за публикацию сообщений в телеграмме'''

import asyncio
# models
from models.data.publicator import Publicator, PublicatorStates, PublicatorModes
from models.data.channel import Channel
from models.data.post import Post


class TGPublicator():
    def __init__(self, db_key: int, task: asyncio.Task, state: int):
        self.task = task
        self.db_key = db_key
        self.state = state

    @classmethod
    def public_post(cls, tg_channel_id: int, post_key: int):
        '''Публикует пост из дазы в телеграм-канал'''
        pass

current_publicators = [] # Работающие в текущий момент публикаторы

async def publicating(period: int, tg_channel_id: int, mode: int, parse_task_key = 0, parse_program_key = 0, last_post_id = 0):
    '''Поток публикатора, в котором он периодически получает из базы посты и публикует их в канал'''
    # Получаем посты
    posts=[]
    if mode == PublicatorModes.New:
        # Публикуем новые посты
        # Получаем поcты предназначенные к публикации
        if parse_program_key==0 or parse_program_key==None:
            condition = Post.post_id > last_post_id | Post.parse_task == parse_task_key
        else:
            condition = Post.post_id > last_post_id | Post.parse_program == parse_task_key
        posts = Post.select().where(condition)
    for post in posts:
        pass


    # Спим
    await asyncio.sleep(period)

async def init_current_publicators():
    '''Инициализация публикаторов
    Загрузка данных из базы и запуск потоков публикаторов'''
    # Загружаем данные из базы
    publicators_mld = Publicator.select()
    for publicator_mld in publicators_mld:
        # Получаем канал
        channel = Channel.get_by_id(publicator_mld.channel)
        # Создаем задачу
        publicator_task = asyncio.create_task(publicating(period=publicator_mld.period,
                                                          tg_channel_id=channel,
                                                          mode=publicator_mld.mode,
                                                          parse_task_key=publicator_mld.parse_task,
                                                          parse_program_key=publicator_mld.parse_program,
                                                          last_post_id = publicator_mld.last_post_id), name=publicator_mld.name)
        publicator_obj = TGPublicator(db_key=publicator_mld.get_id(), task=publicator_task, state=publicator_mld.state)
        current_publicators.append(publicator_obj)



