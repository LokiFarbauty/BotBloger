from peewee import *
#
from models.dm_config import db
from models.data.parse_program import ParseProgram
from models.data.parser import Parser

class ParseTask(Model):
    name = TextField() # имя задачи
    program = ForeignKeyField(ParseProgram, backref='tasks') # ссылка на программу
    parser = ForeignKeyField(Parser, backref='tasks') # ссылка на используемый парсер
    #platform = IntegerField()  # платформа с которой парсим, варианты class Platform_types(enum.Enum)
    #pattern = IntegerField() # шаблон парсинга сайта (будет использоваться в будущем)
    #engine = IntegerField() # движок для парсинга сайта (будет использоваться в будущем)
    target_id = CharField() # id цели (для ВК)
    target_name = CharField() # id название цели (для ВК)
    target_url = TextField() # ссылка откуда парсить (для WEB)
    #posting_mode = IntegerField() # режим публикации class Posting_modes(enum.Enum):
    last_post_id = IntegerField() # id последнего спарсеного поста (для ВК)
    filter = CharField() # фильтр (для ВК)
    options = CharField() # произвольные опции
    cr_dt = DateTimeField() # дата создания задачи
    active = BooleanField() # флаг активна задача или нет
    post_num = IntegerField() # количество постов, которое необходимо собрать (для ВК)
    post_start_date = DateTimeField() # собирать посты от этой даты
    post_end_date = DateTimeField() # собирать посты до этой даты
    key_words = TextField() # собирать посты в которые входят данные слова
    forbidden_words = TextField() # запрещенные слова с которыми пост пропускаем
    clear_words = TextField() # слова, которые при парсинге нужно вырезать
    hashtags = TextField() # собирать посты помеченные данными хэштегами
    search_time_limit = IntegerField() # лимит времени на выполнение парсинга
    #task_start_time = DateTimeField() # дата и время запуска задачи на выполнение
    #task_interval = IntegerField() # периодичность запуска задачи
    post_max_text_length = IntegerField() # максимальная длинна поста
    post_min_text_length = IntegerField()  # максимальная длинна поста

    class Meta:
        database = db  # this model uses the "people.db" database

    @classmethod
    def get_task(cls, key=0, name=''):
        try:
            queryes = []
            if key != 0:
                queryes.append(cls.id == key)
            if name != '':
                queryes.append(cls.name == name)
            task = cls.get(*queryes)
            return task
        except Exception as ex:
            return None