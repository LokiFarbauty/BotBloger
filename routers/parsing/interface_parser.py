'''Это клас-интерфейс, которому должны соответствовать все остальные парсеры'''

from abc import ABC, abstractmethod
from dataclasses import dataclass
import aiohttp
import enum


class ParserInterfaceReturns(enum.Enum):
    Not_defined = -1
    PyError = 'неизвестная ошибка'
    ParsingGood = 'парсинг произведен успешно'
    GetVKWallError = 'не удалось получить данные из ВКонтакте'
    NormalizeDataError = 'нормализация данных не удалась'
    NoFreeProxy = 'Нет доступных бесплатных прокси'


@dataclass
class ParseParams:
    # program_id: int = 0
    # task_id: int = 0
    target_name: str = '' # имя ресурса
    target_url: str = '' # ссылка на страничку сайта
    target_id: int = 0 # id ресурса
    target_type: str = 'group' # тип ресурса ВК user, group, ...
    token: str = '' # токен доступа
    login: str = ''  # логин доступа
    password: str = ''  # пароль доступа
    post_count: int = 100 # Количество постов, которое парсить
    offset: int = 0 # начальный сдвиг
    filter: str = 'all'
    use_free_proxy: bool = False
    proxy_url: str = '' # формат "https://10.10.1.10:1080" или "http://user:pass@10.10.1.10:3128/"
    proxy_protocol: str = '' # формат "http", "https", "ftp"



class ParserInterface(ABC):
    name = 'ParserInterface'
    description = ''

    @classmethod
    @abstractmethod
    async def parse(cls, params: ParseParams, session: aiohttp.ClientSession = None):
        return ParserInterfaceReturns.Not_defined

    @classmethod
    @abstractmethod
    async def get_entries_count(cls, params: ParseParams):
        return ParserInterfaceReturns.Not_defined

    @classmethod
    @abstractmethod
    async def parse_archive(cls, params: ParseParams):
        return ParserInterfaceReturns.Not_defined


class APost():
    # Класс для анализатора постов и обмена данными с парсерами
    def __init__(self, post_id, text, views=0, likes=0, dt=0, keywords_might=0,
                 hashtags='', audios=None, videos=None, photos=None, docs=None, links=None, polls=None):
        self.post_id = post_id
        self.text = text
        self.views = views
        self.likes = likes
        self.hashtags = hashtags
        self.text_hash = ''
        self.dt = dt
        self.keywords_might = keywords_might
        if audios==None:
            self.audios=[]
        else:
            self.audios = audios
        if videos==None:
            self.videos=[]
        else:
            self.videos = videos
        if photos==None:
            self.photos=[]
        else:
            self.photos = photos
        if docs==None:
            self.docs=[]
        else:
            self.docs = docs
        if links==None:
            self.links=[]
        else:
            self.links = links
        if polls==None:
            self.polls=[]
        else:
            self.polls = polls

