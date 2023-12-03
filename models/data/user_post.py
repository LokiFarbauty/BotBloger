from peewee import *
#
from models.dm_config import db
from models.data.post import Post
from models.data.user import User

class User_Post(Model):
    # Посты, которые пользователи добавили в избранное
    user = ForeignKeyField(User, backref='user_post', index=True)
    post = ForeignKeyField(Post, backref='user_post')
    class Meta:
        database = db

    @classmethod
    def check_user_post(cls, user: User, post: Post):
        try:
            queryes = []
            queryes.append(cls.user == user)
            queryes.append(cls.post == post)
            el = cls.get(*queryes)
            return el
        except Exception as ex:
            return None

    @classmethod
    def get_user_posts(cls, user: User):
        try:
            res = Post.select().join(cls).where(cls.user == user)
            return res
        except Exception as ex:
            return ex

    @classmethod
    def get_user_posts_count(cls, user: User = None):
        try:
            res = Post.select().join(cls).where(cls.user == user).count()
            return res
        except Exception as ex:
            return ex

    @classmethod
    def del_user_posts(cls, post: Post):
        try:
            user_favorites = cls.delete().where(cls.post == post)
            user_favorites.execute()
            return 0
        except Exception as ex:
            return ex