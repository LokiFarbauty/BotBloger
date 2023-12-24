from peewee import *
import enum
#
from models.dm_config import db
from models.data.channel import Channel
from models.data.user import User
from models.data.bot import Bot
from models.data.parse_program import ParseProgram
from models.data.parse_task import ParseTask

class PublicatorModes(enum.Enum):
    Single = 1 # публиковать один раз случайный пост
    Period = 2 # публиковать периодически случайный пост
    Marketing = 3 # режим рекламная компания публиковать самые рейтинговые из диапазона
    New = 4 # публиковать новые

class Publicator(Model):
    # Программа состоит из нескольких задач
    name = TextField() # имя
    img = CharField() # указатель на изображение
    channel = ForeignKeyField(Channel, backref='publicators', index=True)
    user = ForeignKeyField(User, backref='publicators', index=True)
    parse_program = ForeignKeyField(ParseProgram, backref='publicators', index=True, null=True)
    parse_task = ForeignKeyField(ParseTask, backref='publicators', index=True, null=True)
    mode = IntegerField() # Режим публикации
    period = IntegerField() # Период публикации
    range = IntegerField() # Для режима Marketing - диапазон лучших постов из которых выбирать случайнывй
    bot = ForeignKeyField(Bot, backref='publicators', index=True)

    class Meta:
        database = db

    @classmethod
    def get_publicator(cls, key=0, name='', channel_id=0):
        try:
            queryes = []
            if key != 0:
                queryes.append(cls.id == key)
            if name != '':
                queryes.append(cls.name == name)
            if channel_id != 0:
                queryes.append(cls.channel == channel_id)
            publicator = cls.get(*queryes)
            return publicator
        except Exception as ex:
            return None