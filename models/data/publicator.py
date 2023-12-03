from peewee import *
import enum
#
from models.dm_config import db
from models.data.channel import Channel
from models.data.user import User
from models.data.bot import Bot
from models.data.parse_program import ParseProgram

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
    mode = IntegerField() # Режим публикации
    period = IntegerField() # Период публикации
    range = IntegerField() # Для режима Marketing - диапазон лучших постов из которых выбирать случайнывй
    bot = ForeignKeyField(Bot, backref='publicators', index=True)


    class Meta:
        database = db

