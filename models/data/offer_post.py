from peewee import *
#
from models.dm_config import db
from models.data.user import User

class Offer_Post(Model):
    # Посты, которые пользователи предложили для публикации
    user = ForeignKeyField(User, backref='offer_post', index=True)
    text = TextField()
    img_url = TextField()
    dt = DateTimeField()
    class Meta:
        database = db