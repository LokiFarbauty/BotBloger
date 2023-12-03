
from peewee import *
#
from models.dm_config import db
from models.data.user import User
from models.data.parse_program import ParseProgram

class User_ParseProgram(Model):
    user = ForeignKeyField(User, backref='users_program')
    program = ForeignKeyField(ParseProgram, backref='users_program')
    class Meta:
        database = db  # this model uses the "people.db" database