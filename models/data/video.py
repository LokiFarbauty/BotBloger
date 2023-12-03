from peewee import *
#
from models.dm_config import db
from models.data.post import Post

class Video(Model):
    owner = ForeignKeyField(Post, backref='videos', index=True)
    url = TextField()
    file = TextField()
    file_id = TextField()
    caption = TextField()
    description = TextField()
    class Meta:
        database = db