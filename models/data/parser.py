from peewee import *
#
from models.dm_config import db
from models.data.user import User

class Parser(Model):
    name = CharField()
    platform = CharField() # Название типа парсера, например ВКонтакте
    user = ForeignKeyField(User, backref='parsers') # пользователь, которому принадлежит парсер
    img = TextField()
    file = TextField()
    description = TextField()
    login = TextField(null=True)
    password = TextField(null=True)
    token = TextField(null=True)
    public = BooleanField() # 1 - публичный парсер, может быть использован любым пользователем


    class Meta:
        database = db