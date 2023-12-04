from peewee import *
#
from models.dm_config import db
from models.data.post import Post

class Video(Model):
    owner = ForeignKeyField(Post, backref='videos', index=True)
    url = TextField()
    file = TextField(null=True)
    file_id = TextField(null=True)
    title = TextField()
    description = TextField()
    class Meta:
        database = db