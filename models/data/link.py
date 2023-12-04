from peewee import *
#
from models.dm_config import db
from models.data.post import Post

class Link(Model):
    owner = ForeignKeyField(Post, backref='links', index=True)
    url = TextField()
    description = TextField()
    title = TextField()
    class Meta:
        database = db

    @classmethod
    def get_post_link(cls, post: Post):
        try:
            queryes=[]
            queryes.append(cls.owner == post)
            el = cls.get(*queryes)
            return el
        except Exception as ex:
            return None