from peewee import *
import enum
#
from models.dm_config import db
from models.data.user import User

class ChannelTypes(enum.Enum):
    Public = 0
    Dump = 1
    Error = 2
    Info = 3

class Channel(Model):
    user = ForeignKeyField(User, backref='users', index=True)
    id = IntegerField()
    type = IntegerField()
    name = TextField()
    url = TextField()

    class Meta:
        database = db