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
    VkSync = 4

class Channel(Model):
    channel_tg_id = IntegerField()
    user = ForeignKeyField(User, backref='users', index=True)
    type = IntegerField()
    name = TextField()
    url = TextField()

    class Meta:
        database = db

    @classmethod
    def get_channel(cls, user=0, name='', url='', channel_id=0):
        try:
            queryes = []
            if user != 0:
                queryes.append(cls.user == user)
            if name != '':
                queryes.append(cls.name == name)
            if url != '':
                queryes.append(cls.url == url)
            if channel_id != 0:
                queryes.append(cls.channel_tg_id == channel_id)
            publicator = cls.get(*queryes)
            return publicator
        except Exception as ex:
            return None

    @classmethod
    def get_channel_or_make(cls, channel_id, channel_name, user: User):
        channel = Channel.get_channel(channel_id=channel_id, name=channel_name, user=user)
        if channel == None:
            channel = Channel.create(name=channel_name, user=user, channel_tg_id=channel_id, url='',
                                     type=ChannelTypes.Public.value)
            channel.save()
        return channel