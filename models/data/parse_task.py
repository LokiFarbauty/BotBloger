from peewee import *
import enum
#
from models.dm_config import db
from models.data.parse_program import ParseProgram
from models.data.parser import Parser
from models.data.user import User
from models.data.criterion import Criterion

class ParseTaskStates(enum.Enum):
    Stopped = 0  # задача остановлена
    InWork = 1  # задача в работе
    Ended = 2 # завершено успешно
    Error = 3 # завершено с ошибкой

class ParseTaskActive(enum.Enum):
    Stopped = 0 # задача остановлена
    InWork = 1 # задача в работе

class ParseTask(Model):
    name = TextField() # имя задачи
    user = ForeignKeyField(User, backref='tasks', null=True) # ссылка на пользователя создавшего задачу
    program = ForeignKeyField(ParseProgram, backref='tasks', null=True) # ссылка на программу
    parser = ForeignKeyField(Parser, backref='tasks', null=True) # ссылка на используемый парсер
    criterion = ForeignKeyField(Criterion, backref='tasks')  # ссылка на критерии выборки
    #platform = IntegerField()  # платформа с которой парсим, варианты class Platform_types(enum.Enum)
    #pattern = IntegerField() # шаблон парсинга сайта (будет использоваться в будущем)
    #engine = IntegerField() # движок для парсинга сайта (будет использоваться в будущем)
    target_id = CharField(null=True) # id цели (для ВК)
    target_name = CharField(null=True) # id название цели (для ВК)
    target_url = TextField(null=True) # ссылка откуда парсить (для WEB)
    target_type = CharField(null=True) # тип цели (в ВК: user, group ...)
    #posting_mode = IntegerField() # режим публикации class Posting_modes(enum.Enum):
    last_post_id = IntegerField() # id последнего спарсеного поста (для ВК)
    filter = CharField(null=True) # фильтр (для ВК)
    options = CharField(null=True) # произвольные опции
    cr_dt = DateTimeField() # дата создания задачи
    active = IntegerField()  # флаг автостарта (используется для автозапуска)
    post_num = IntegerField() # количество постов, которое необходимо собрать (для ВК)
    # post_start_date = DateTimeField(null=True) # собирать посты от этой даты
    # post_end_date = DateTimeField(null=True) # собирать посты до этой даты
    #key_words = TextField(null=True) # собирать посты в которые входят данные слова
    #forbidden_words = TextField(null=True) # запрещенные слова с которыми пост пропускаем
    #clear_words = TextField(null=True) # слова, которые при парсинге нужно вырезать
    #hashtags = TextField(null=True) # собирать посты помеченные данными хэштегами
    period = IntegerField() # периодичность запуска задачи, 0 - единичное выполнение
    #task_start_time = DateTimeField() # дата и время запуска задачи на выполнение
    #task_interval = IntegerField() # периодичность запуска задачи
    #post_max_text_length = IntegerField(null=True) # максимальная длинна поста
    #post_min_text_length = IntegerField(null=True)  # максимальная длинна поста
    state = IntegerField()  # Результат последнего запуска задачи
    error = TextField(null=True)  # Последняя ошибка задачи

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