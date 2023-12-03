from peewee import *
#
from models.dm_config import db
from models.data.audio import Audio
from models.data.bot import Bot

class AudioUpload(Model):
    audio = ForeignKeyField(Audio, backref='audiouploads', index=True)
    bot = ForeignKeyField(Bot, backref='audiouploads', index=True, null=True)
    file_id = TextField()

    class Meta:
        database = db

    @classmethod
    def get_audio_upload(cls, audio: Audio, bot: Bot):
        try:
            queryes = []
            queryes.append(cls.audio == audio)
            queryes.append(cls.bot == bot)
            el = AudioUpload.get(*queryes)
            return el
        except Exception as ex:
            return None