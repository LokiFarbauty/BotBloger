from peewee import *
import enum
#
from models.dm_config import db
from models.data.parse_program import ParseProgram
from models.data.parser import Parser

class ParseTaskStates(enum.Enum):
    Good = 0 # завершено успешно
    Error = 1 # завершено с ошибкой

class ParseTask(Model):
    name = TextField() # имя задачи
    program = ForeignKeyField(ParseProgram, backref='tasks', null=True) # ссылка на программу
    parser = ForeignKeyField(Parser, backref='tasks', null=True) # ссылка на используемый парсер
    #platform = IntegerField()  # платформа с которой парсим, варианты class Platform_types(enum.Enum)
    #pattern = IntegerField() # шаблон парсинга сайта (будет использоваться в будущем)
    #engine = IntegerField() # движок для парсинга сайта (будет использоваться в будущем)
    target_id = CharField(null=True) # id цели (для ВК)
    target_name = CharField(null=True) # id название цели (для ВК)
    target_url = TextField(null=True) # ссылка откуда парсить (для WEB)
    #posting_mode = IntegerField() # режим публикации class Posting_modes(enum.Enum):
    last_post_id = IntegerField() # id последнего спарсеного поста (для ВК)
    filter = CharField(null=True) # фильтр (для ВК)
    options = CharField(null=True) # произвольные опции
    cr_dt = DateTimeField() # дата создания задачи
    active = BooleanField() # флаг активна задача или нет
    post_num = IntegerField(null=True) # количество постов, которое необходимо собрать (для ВК)
    post_start_date = DateTimeField(null=True) # собирать посты от этой даты
    post_end_date = DateTimeField(null=True) # собирать посты до этой даты
    key_words = TextField(null=True) # собирать посты в которые входят данные слова
    forbidden_words = TextField(null=True) # запрещенные слова с которыми пост пропускаем
    clear_words = TextField(null=True) # слова, которые при парсинге нужно вырезать
    hashtags = TextField(null=True) # собирать посты помеченные данными хэштегами
    search_time_limit = IntegerField(null=True) # лимит времени на выполнение парсинга
    #task_start_time = DateTimeField() # дата и время запуска задачи на выполнение
    #task_interval = IntegerField() # периодичность запуска задачи
    post_max_text_length = IntegerField(null=True) # максимальная длинна поста
    post_min_text_length = IntegerField(null=True)  # максимальная длинна поста
    state = IntegerField()  # Результат последнего запуска задачи
    error = TextField()  # Последняя ошибка задачи

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

    def save_last_post_id(self, last_post_id: int):
        self.last_post_id = last_post_id
        self.save()