from peewee import *
#
from models.dm_config import db
from models.data.post import Post

class Doc(Model):
    owner = ForeignKeyField(Post, backref='docs', index=True)
    url = TextField()
    class Meta:
        database = db