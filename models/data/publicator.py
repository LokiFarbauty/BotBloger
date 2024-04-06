from peewee import *
import enum
#
from models.dm_config import db
from models.data.channel import Channel
from models.data.user import User
from models.data.bot import Bot
from models.data.parse_program import ParseProgram
from models.data.parse_task import ParseTask
from models.data.criterion import Criterion

class PublicatorModes(enum.Enum):
    NotSet = 0  # не задан
    Single = 1 # публиковать один раз случайный пост
    Period = 2 # публиковать периодически случайный пост
    Marketing = 3 # режим рекламная компания публиковать самые рейтинговые из диапазона
    New = 4 # публиковать новые
    Premoderate = 5 # публиковать отмеченные в премодерации посты начиная с самой поздней даты, после публикации помечаем пост к удалению либо в архив

class PublicatorStates(enum.Enum):
    Stopped = 0 # публикатор остановлен
    Working = 1 # публикатор работает
    Stopped_Error = 2 # остановлекн из-за ошибки
    Done = 3 # завершил работу


class Publicator(Model):
    # Программа состоит из нескольких задач
    name = TextField() # имя
    img = CharField(null=True) # указатель на изображение
    channel = ForeignKeyField(Channel, backref='publicators', index=True)
    user = ForeignKeyField(User, backref='publicators', index=True)
    cr_dt = DateTimeField() # дата создания
    parse_program = ForeignKeyField(ParseProgram, backref='publicators', index=True, null=True)
    parse_task = ForeignKeyField(ParseTask, backref='publicators', index=True, null=True)
    criterion = ForeignKeyField(Criterion, backref='tasks')  # ссылка на критерии выборки
    mode = IntegerField(default=0) # Режим публикации
    autostart = IntegerField(default=0) # Автозапуск 1 - да 0 нет
    period = IntegerField(default=0) # Период публикации
    start_delay = IntegerField(default=60) # Задержка публикации перед стартом публикатора
    public_delay = IntegerField(default=60) # Задержка между публикациями постов
    start_public_hour = IntegerField(default=9)  # время начала публикаций
    end_public_hour = IntegerField(default=20)  # время окончания публикаций
    range = IntegerField(null=True) # Для режима Marketing - диапазон лучших постов из которых выбирать случайный
    delete_public_post = IntegerField(default=0) # Если 1 то после публикации пост удаляется из базы
    bot = ForeignKeyField(Bot, backref='publicators', index=True)
    telegraph_token = CharField()  # токен Телеграф
    author_caption = TextField(default="") # авторская подпись (выкладывается в конце поста)
    author_name = CharField(default="") # имя автора (для страничек Телеграф)
    author_url = CharField(default="")  # ссылка на автора (для страничек Телеграф)
    #premoderate = IntegerField(default=0)  # флаг премодерации, если установлен пост отправить на премодерацию админу
    state = IntegerField() # Состояние публикатора
    error = TextField(null=True) # Последняя ошибка публикатора (Причина остановки его работы)
    last_post_id = IntegerField(default=0) # vk_id последнего опубликованного поста

    class Meta:
        database = db

    @classmethod
    def get_publicator(cls, key=0, name='', channel=0, user=0):
        try:
            queryes = []
            if key != 0:
                queryes.append(cls.id == key)
            if name != '':
                queryes.append(cls.name == name)
            if channel != 0:
                queryes.append(cls.channel == channel)
            if user != 0:
                queryes.append(cls.user == user)
            publicator = cls.get(*queryes)
            return publicator
        except Exception as ex:
            return None