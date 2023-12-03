from peewee import *

#
from models.dm_config import db
from models.data.user import User

class Bot(Model):
    user = ForeignKeyField(User, backref='bots', index=True)
    token = TextField()
    parse_mode = CharField()
    name = TextField()
    url = TextField()
    active = BooleanField()
    public = BooleanField()  # доступен ли бот для всех, ели нет то доступ будет только у пользователя
    class Meta:
        database = db

    @classmethod
    def make(cls, user: User, token, parse_mode: str, name: str, url: str, active: int, public: int):
        # Проверяем есть ли уже такой бот
        bot = cls.select().where(cls.token==token)
        try:
            element=bot[0]
            return element
        except Exception as ex:
            # Если нет то создаем
            element = cls.create(user=user, token=token, parse_mode=parse_mode, name=name, url=url, active=active, public=public)
            element.save()
            return element

    @classmethod
    def get_obj(cls, token: str):
        try:
            queryes = []
            queryes.append(cls.token == token)
            el = cls.get(*queryes)
            return el
        except Exception as ex:
            return None

    def refresh_bot_info(self, name: str, url: str):
        try:
            self.name = name
            self.url = url
            self.save()
            return self
        except Exception as ex:
            return ex