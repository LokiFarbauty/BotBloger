from datetime import datetime
from peewee import *
#
from models.dm_config import db
from models.data.user import User
from models.data.parser import Parser

class User_Parser(Model):
    '''Парсеры доступные пользователю'''
    user = ForeignKeyField(User, backref='users_parsers')
    parser = ForeignKeyField(Parser, backref='users_parsers')
    class Meta:
        database = db  # this model uses the "people.db" database

    @classmethod
    def get_obj(cls, user: User, bot: Parser):
        try:
            queryes = []
            queryes.append(cls.user == user)
            queryes.append(cls.bot == bot)
            el = cls.get(*queryes)
            return el
        except Exception as ex:
            return None