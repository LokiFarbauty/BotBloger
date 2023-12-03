from peewee import *
#
from models.dm_config import db

class Parser(Model):
    name = CharField()
    img = TextField()
    file = TextField()
    description = TextField()
    login = TextField()
    password = TextField()
    token = TextField()

    class Meta:
        database = db