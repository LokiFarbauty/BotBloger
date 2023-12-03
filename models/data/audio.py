from peewee import *
#
from models.dm_config import db
from models.data.post import Post

class Audio(Model):
    owner = ForeignKeyField(Post, backref='audios', index=True)
    url = TextField()
    file_id = TextField()
    artist = CharField()
    title = CharField()
    class Meta:
        database = db

