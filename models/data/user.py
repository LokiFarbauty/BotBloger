from peewee import *
from datetime import datetime
#
from models.dm_config import db
# from models.data.bot import Bot
from models.data.hashtag import Hashtag


class User(Model):
    tg_user_id = IntegerField(index=True)
    username = CharField()
    firstname = CharField()
    lastname = CharField()
    first_visit = DateTimeField()
    last_visit = DateTimeField()
    #last_post_read = ForeignKeyField(Post, backref='user', null=True)
    #last_hashtag_read = ForeignKeyField(Hashtag, backref='user', null=True)
    permissions = TextField()
    balance = FloatField()

    class Meta:
        database = db

    @classmethod
    def get_user(cls, user_key = 0, user_tg_id = 0, user_name = ''):
        try:
            queryes = []
            if user_key != 0:
                queryes.append(cls.id == user_key)
            if user_tg_id != 0:
                queryes.append(cls.tg_user_id == user_tg_id)
            if user_name != '':
                queryes.append(cls.username == user_name)
            el = cls.get(*queryes)
            return el
        except Exception as ex:
            return None

    @classmethod
    def get_users_obj(cls, par) -> list:
        '''Возвращает список пользователей'''
        elements = []
        try:
            users = User.select().where(User.tg_user_id == par)
            for user in users:
                elements.append(user)
        except Exception as ex:
            pass
        try:
            users = User.select().where(User.username == par)
            for user in users:
                elements.append(user)
        except Exception as ex:
            pass
        return elements

