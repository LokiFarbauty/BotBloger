from peewee import *
#
from models.dm_config import db
from models.data.parse_task import ParseTask

class Post(Model):
    post_id = IntegerField()
    source_id = IntegerField(index=True)
    text = IntegerField(index=True)
    views = IntegerField()
    old_views = IntegerField()
    likes = IntegerField(index=True)
    dt = DateTimeField(index=True)
    in_telegraph = IntegerField()
    telegraph_url = CharField()
    text_hash = TextField(index=True)
    parse_task = ForeignKeyField(ParseTask, backref='posts', null=True)
    published = BooleanField()
    last_published_dt = DateTimeField(index=True)

    class Meta:
        database = db

    @classmethod
    def get_post(cls, post_id: int = 0, source_id: int = 0, text_hash: str = '', text_id: int = 0):
        try:
            queryes = []
            if post_id != 0:
                queryes.append(cls.post_id == post_id)
            if source_id != 0:
                queryes.append(cls.source_id == source_id)
            if text_hash != '':
                queryes.append(cls.text_hash == text_hash)
            if text_id != 0:
                queryes.append(cls.text == text_id)
            el = cls.get(*queryes)
            return el
        except Exception as ex:
            return None

    def increase_post_views(self):
        self.views += 1
        self.save()