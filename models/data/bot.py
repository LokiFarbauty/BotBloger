from peewee import *
import enum

#
from models.dm_config import db
from models.data.user import User

class BotStates(enum.Enum):
    Stopped = 0  # задача остановлена
    InWork = 1  # задача в работе
    Error = 2 # завершено с ошибкой

class Bot(Model):
    user = ForeignKeyField(User, backref='bots', index=True)
    token = TextField()
    parse_mode = CharField()
    name = TextField()
    url = TextField()
    tg_id = IntegerField()
    active = BooleanField() # Переменная автозапуска для бота
    state = IntegerField() # состояние бота
    public = BooleanField()  # доступен ли бот для всех, ели нет то доступ будет только у пользователя
    db_file = TextField()
    class Meta:
        database = db

    @classmethod
    def make(cls, user: User, token, parse_mode: str, name: str, url: str, active: int, public: int, tg_id: int, db_file: str):
        # Проверяем есть ли уже такой бот
        bot = cls.select().where(cls.token==token)
        try:
            element=bot[0]
            return element
        except Exception as ex:
            # Если нет то создаем
            element = cls.create(user=user, token=token, parse_mode=parse_mode, name=name, url=url, active=active,
                                 state=BotStates.Stopped.value, public=public, tg_id=tg_id, db_file=db_file)
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

    @classmethod
    def get_bot(cls, key=0, name='', url='', tg_id=0):
        try:
            queryes = []
            if key != 0:
                queryes.append(cls.id == key)
            if name != '':
                queryes.append(cls.name == name)
            if url != '':
                queryes.append(cls.url == url)
            if tg_id != 0:
                queryes.append(cls.tg_id == tg_id)
            bot = cls.get(*queryes)
            return bot
        except Exception as ex:
            return None

    def refresh_bot_info(self, state: int, name: str='', url: str='', tg_id: int=0):
        try:
            if name != '':
                self.name = name
            if url != '':
                self.url = url
            if tg_id != 0:
                self.tg_id = tg_id
            self.state = state
            self.save()
            return self
        except Exception as ex:
            return ex