from datetime import datetime
from peewee import *
#
from models.dm_config import db
from models.data.user import User
from models.data.bot import Bot

class User_Bot(Model):
    user = ForeignKeyField(User, backref='users_bots')
    bot = ForeignKeyField(Bot, backref='users_bots')
    class Meta:
        database = db  # this model uses the "people.db" database

    @classmethod
    def get_obj(cls, user: User, bot: Bot):
        try:
            queryes = []
            queryes.append(cls.user == user)
            queryes.append(cls.bot == bot)
            el = cls.get(*queryes)
            return el
        except Exception as ex:
            return None

    @classmethod
    def check_user(cls, bot, user_tg_id: int, username: str = '', firstname='', lastname=''):
        user = User.get_user(user_tg_id=user_tg_id)
        ts_now = datetime.now().replace(microsecond=0)
        ts_now = ts_now.timestamp()
        if user == None:
            user = User.create(tg_user_id=user_tg_id, username=username, firstname=firstname, lastname=lastname,
                               first_visit=ts_now, last_visit=0, balance=0)
        else:
            user.last_visit = ts_now
        user.save()
        # Связываем пользователя с ботом
        # Проверяем была ли связь
        if bot != None:
            user_bot = cls.get_obj(user=user, bot=bot)
            if user_bot == None:
                user_bot = cls.create(user=user, bot=bot)
                user_bot.save()
        return user