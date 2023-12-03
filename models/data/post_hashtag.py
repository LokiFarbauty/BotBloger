from peewee import *
#
from models.dm_config import db
from models.data.post import Post
from models.data.hashtag import Hashtag

class Post_Hashtag(Model):
    post = ForeignKeyField(Post, backref='post_hashtag')
    hashtag = ForeignKeyField(Hashtag, backref='post_hashtag', index=True)
    class Meta:
        database = db

    @classmethod
    def get_post_hashtags_str(cls, post: Post) -> str:
        phs = cls.select().where(cls.post == post)
        hashtags = ''
        for ph in phs:
            htg = ph.hashtag.value
            hashtags = f'{hashtags}, {htg}'
        return hashtags[2:]