from peewee import *
#
from models.dm_config import db
from models.data.post import Post

class Poll(Model):
    owner = ForeignKeyField(Post, backref='polls', index=True)
    question = TextField()
    answers = TextField()
    options = TextField()
    anonymous = BooleanField()
    multiple = BooleanField()

    class Meta:
        database = db