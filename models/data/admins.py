from datetime import datetime
from peewee import *
#
from models.dm_config import db
from models.data.user import User
from models.data.publicator import Publicator

class Admins(Model):
    '''Администраторы'''
    user = ForeignKeyField(User, backref='admins')
    publicator = ForeignKeyField(Publicator, backref='admins')
    class Meta:
        database = db  # this model uses the "people.db" database

    @classmethod
    def get_obj(cls, user: User, publicator: Publicator):
        try:
            queryes = []
            queryes.append(cls.user == user)
            queryes.append(cls.publicator == publicator)
            el = cls.get(*queryes)
            return el
        except Exception as ex:
            return None