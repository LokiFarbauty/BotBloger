from peewee import *
import enum
#
from models.dm_config import db
from models.data.parse_task import ParseTask
from models.data.parse_program import ParseProgram

class ModerateStates(enum.Enum):
    NotModerate = 0  # не модерируется и не публиковался
    NotVerified = 1  # ожидает верификации
    ToPublish = 2  # ждет публикации
    Published = 3 # опубликован
    InArchive = 4 # отправлен в архив
    ToDelete = 5  # На удаление

class LanguageStates(enum.Enum):
    RUS = 'ru' #
    ENG = 'en' #
    CHN = 'zh_Hans'
    ISP = 'es'
    IND = 'hi'
    PTG = 'pt'
    GER = 'de'
    FRA = 'fr'
    UKR = 'uk'
    KOR = 'ko'
    POL = 'pl'
    TUR = 'tr'

class Post(Model):
    post_id = IntegerField()
    source_id = IntegerField(index=True)
    text = IntegerField(index=True)
    views = IntegerField()
    old_views = IntegerField()
    likes = IntegerField(index=True)
    rate = FloatField(index=True, default=0)
    dt = DateTimeField(index=True)
    telegraph_url = CharField()
    text_hash = TextField(index=True)
    text_len = IntegerField(index=True)
    parse_task = ForeignKeyField(ParseTask, backref='posts', null=True)
    parse_program = ForeignKeyField(ParseProgram, backref='posts', null=True)
    last_published_dt = DateTimeField(index=True) # дата публикации поста
    moderate = IntegerField(default=0) # флаг премодерации
    translation = CharField(default='ru') # Указание следует ли переводить пост на другой язык

    class Meta:
        database = db

    @classmethod
    def get_post(cls, post_id: int = 0, task_id: int = 0, source_id: int = 0, text_hash: str = '', text_id: int = 0):
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
            if task_id != 0:
                queryes.append(cls.parse_task == task_id)
            el = cls.get(*queryes)
            return el
        except Exception as ex:
            return None

    # def get_post_hashtags_str(self) -> str:
    #     #phs = Post_Hashtag.select().where(Post_Hashtag.post == post)
    #     phs = Post_Hashtag.select().where(Post_Hashtag.post == self)
    #     hashtags = ''
    #     for ph in phs:
    #         htg = ph.hashtag.value
    #         hashtags = f'{hashtags}, {htg}'
    #     return hashtags[2:]

    def increase_post_views(self):
        self.views += 1
        self.save()



