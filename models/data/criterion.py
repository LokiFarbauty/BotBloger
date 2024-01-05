from peewee import *
import enum
#
from models.dm_config import db

class VideoPlatform(enum.Enum):
    All = 0
    Ignore = 1
    OnlyYouTube = 2
    OnlyVK = 3

class UrlAction(enum.Enum):
    Accept = 0 # Оставлять ссылки
    Ignore = 1 # С сылками не парсить
    Delete = 2 # удалять ссылки


class Criterion(Model):
    target_id = CharField(null=True) # id цели (для ВК)
    target_name = CharField(null=True) # id название цели (для ВК)
    target_url = TextField(null=True) # ссылка откуда парсить (для WEB)
    target_type = CharField(null=True) # тип цели (в ВК: user, group ...)
    options = CharField(null=True) # произвольные опции
    key_words = TextField(null=True) # собирать посты в которые входят данные слова
    forbidden_words = TextField(null=True) # запрещенные слова с которыми пост пропускаем
    clear_words = TextField(null=True) # слова, которые при парсинге нужно вырезать
    hashtags = TextField(null=True) # собирать посты помеченные данными хэштегами
    post_max_text_length = IntegerField(null=True) # максимальная длинна поста
    post_min_text_length = IntegerField(null=True)  # максимальная длинна поста
    post_start_date = DateTimeField(null=True) # собирать посты от этой даты
    post_end_date = DateTimeField(null=True) # собирать посты до этой даты
    check_mat = IntegerField(default=0)  # проверять ли на наличие мата
    video_platform = IntegerField(null=True)  # проверять ли на соответствие видеоплатформе
    del_hashtags = BooleanField(default=0)  # проверять ли на соответствие видеоплатформе
    url_action = IntegerField(default=0)  # Что делать с текстом в котором есть ссылки

    class Meta:
        database = db  # this model uses the "people.db" database

    @classmethod
    def get_criterion(cls, key=0):
        try:
            queryes = []
            if key != 0:
                queryes.append(cls.id == key)
            criterion = cls.get(*queryes)
            return criterion
        except Exception as ex:
            return None