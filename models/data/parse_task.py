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
    Sleep = 2  # ждет
    Ended = 3 # завершено успешно
    Error = 4 # завершено с ошибкой

class ParseTaskActive(enum.Enum):
    Stopped = 0 # задача остановлена
    InWork = 1 # задача в работе

class ParseModes(enum.Enum):
    UNKNOWN = 0
    ARCHIVE = 1  # парсить все посты
    UPDATE_PERIOD = 2 #
    UPDATE_SINGLE = 3 #
    COUNT = 4 #


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
    mode = IntegerField(default=0) # режим парсинга ParseModes - на данный момент не задействовано, ни на что не влияет, режим определяется параметрами периода и количества постов
    last_post_id = IntegerField() # id последнего спарсеного поста (для ВК)
    filter = CharField(null=True) # фильтр (для ВК)
    options = TextField(null=True) # произвольные опции
    def_lang = TextField(default='ru') # Язык поста по умолчанию
    cr_dt = DateTimeField() # дата создания задачи
    active = IntegerField(default=0)  # флаг автостарта (используется для автозапуска)
    start_parse_hour = IntegerField(default=0)  # время начала парсинга
    end_parse_hour = IntegerField(default=6)  # время окончания парсинга
    post_num = IntegerField() # количество постов, которое необходимо собрать (для ВК)
    period = IntegerField(default=0) # периодичность запуска задачи, 0 - единичное выполнение
    moderated = IntegerField(default=0) # флаг модерируемости, если 1 - то спасеные почты будут помечаться как ожидающие модерации
    max_not_moderated_posts = IntegerField(default=0) # Максимум нерассмотренных постов для премодерируемых задач
    state = IntegerField() # Результат последнего запуска задачи
    error = TextField(null=True) # Последняя ошибка задачи
    avg_post_rate = FloatField(default=0) # Технический параметр для расчета рейтинга поста - расчитывается сам, менять в ручную не надо
    max_post_rate = FloatField(default=0) # Технический параметр для расчета рейтинга поста - расчитывается сам, менять в ручную не надо
    min_post_rate = FloatField(default=0) # Технический параметр для расчета рейтинга поста - расчитывается сам, менять в ручную не надо
    posts_remains = IntegerField(default=0)  # Технический параметр - трогать не надо, определяет количество сделаных циклов парсинга (при парсинге архива)



    class Meta:
        database = db  # this model uses the "people.db" database

    @classmethod
    def get_task(cls, key=0, name='', user=0, target_id=0):
        try:
            queryes = []
            if key != 0:
                queryes.append(cls.id == key)
            if name != '':
                queryes.append(cls.name == name)
            if user != 0:
                queryes.append(cls.user == user)
            if target_id != 0:
                queryes.append(cls.target_id == target_id)
            task = cls.get(*queryes)
            return task
        except Exception as ex:
            return None

    def save_last_post_id(self, last_post_id: int):
        self.last_post_id = last_post_id
        self.save()

    async def refresh_task_state(self, state, error=None):
        # Обновление состояния задачи
        try:
            self.state = state
            self.error = error
            self.save()
        except:
            pass