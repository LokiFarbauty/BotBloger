from peewee import *
#
from models.dm_config import db

class Hashtag(Model):
    value = CharField()
    class Meta:
        database = db

    @classmethod
    def get_hashtag(cls, hashtag: str):
        try:
            queryes = []
            queryes.append(cls.value == hashtag)
            el = cls.get(*queryes)
            return el
        except Exception as ex:
            return None