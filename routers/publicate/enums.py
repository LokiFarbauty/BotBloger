
import enum


class PublicateErrors(enum.Enum):
    NoError = 'опубликовано без ошибок'
    BotError = 'ошибка бота'
    MatError = 'в посте обнаружены запрещенные слова, он не опубликован'
    TGPHError = 'не удалось опубликовать пост в Телеграф'
    OtherError = 'неизвестная ошибка, смотрите логи'

class PBTaskStatus(enum.Enum):
    Done = 'выполнена'
    Cancelled = 'остановлена'
    Active = 'выполняется'
    NotFound = 'не найдена'

class PostTextlen(enum.Enum):
    Short = 950 # длинна текста до 1000 символов
    Medium = 2500
    Long = 4000

class PostVideos(enum.Enum):
    No = 0
    Single = 1
    Seria = 2

class PostAudios(enum.Enum):
    No = 0
    Single = 1
    Seria = 2

class PostLinks(enum.Enum):
    No = 0
    Single = 1
    Seria = 2

class PostDocs(enum.Enum):
    No = 0
    Single = 1
    Seria = 2

class PostPolls(enum.Enum):
    No = 0
    Single = 1

class PostImgs(enum.Enum):
    No = 0
    Single = 1
    Seria = 2