
from peewee import *
#
from models.dm_config import db
from models.data.post import Post

class Photo(Model):
    owner = ForeignKeyField(Post, backref='photos', index=True)
    url = TextField()
    caption = TextField()
    class Meta:
        database = db

    @classmethod
    def get_post_photo(cls, post: Post):
        try:
            queryes=[]
            queryes.append(cls.owner == post)
            el = cls.get(*queryes)
            return el
        except Exception as ex:
            return None