from peewee import *
#
from models.dm_config import db
from models.data.user import User

class Parser(Model):
    name = CharField()
    platform = CharField() # Название типа парсера, например ВКонтакте
    platform_user_id = IntegerField(null=True)
    platform_user_name = CharField(null=True)
    user = ForeignKeyField(User, backref='parsers') # пользователь, которому принадлежит парсер
    img = TextField(null=True)
    file = TextField(null=True)
    description = TextField(null=True)
    login = TextField(null=True)
    password = TextField(null=True)
    token = TextField(null=True)
    cr_dt = DateTimeField()  # дата создания
    public = BooleanField() # 1 - публичный парсер, может быть использован любым пользователем

    class Meta:
        database = db

    @classmethod
    def get_parser(cls, user = 0, token = '', platform_user_id = 0, platform_user_name = ''):
        try:
            queryes = []
            if user != 0:
                queryes.append(cls.user == user)
            if platform_user_id != 0:
                queryes.append(cls.platform_user_id == platform_user_id)
            if token != '':
                queryes.append(cls.token == token)
            if platform_user_name != '':
                queryes.append(cls.platform_user_name == platform_user_name)
            el = cls.get(*queryes)
            return el
        except Exception as ex:
            return None

    @classmethod
    def get_service_parser(cls):
        try:
            queryes = []
            queryes.append(cls.name == 'service_parser')
            el = cls.get(*queryes)
            return el
        except Exception as ex:
            return None
