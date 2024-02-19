from peewee import *
#
from models.dm_config import db
from models.data.user import User

class ParseProgram(Model):
    # Программа состоит из нескольких задач
    name = TextField() # имя
    cr_dt = DateTimeField(default=0) # дата создания
    img = CharField(null=True) # указатель на изображение
    #user = ForeignKeyField(User, backref='parse_programs', index=True)
    description = TextField(default='') # описание

    class Meta:
        database = db

    @classmethod
    def get_program(cls, key = 0, name = '', user: User = None):
        # task = Task.select().where(Task.id == 1).get()
        try:
            queryes = []
            if key != 0:
                queryes.append(cls.id == key)
            if name != '':
                queryes.append(cls.name == name)
            if user != None:
                queryes.append(cls.user == user)
            program = cls.get(*queryes)
            return program
        except Exception as ex:
            return None