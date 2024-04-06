from peewee import *
import enum
#
from models.dm_config import db
from models.data.channel import Channel
#
# class ChannelTypes(enum.Enum):
#     Public = 0
#     Dump = 1
#     Error = 2
#     Info = 3
#     VkSync = 4

class TwinChannel(Model):
    owner_channel = ForeignKeyField(Channel, backref='channels', index=True)
    channel_tg_id = IntegerField()
    name = TextField()
    url = TextField(null=True)
    language = TextField(default='en') # LanguageStates

    class Meta:
        database = db

    @classmethod
    def get_twins_channels(cls, channel: Channel):
        try:
            twins_channels = TwinChannel.select().where(cls.owner_channel == channel)
            return twins_channels
        except Exception as ex:
            return None