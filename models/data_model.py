'''Это модуль данных, он отвечает за автоматическое создание моделей данных в базе.
При импорте этого модуля автоматически создается база и пользователеть - суперадмин.
Для добавления моделей просто создайте файл с моделью в папке data.
Модуль сам создаст соответствующую таблицу в базе'''

from peewee import Model
from playhouse.sqlite_ext import FTS5Model, FTSModel
from os import listdir
from os.path import isfile, join
import enum
import importlib
import inspect
#
import models.dm_config as dm_config
from models.data.user import User
from models.data.parser import Parser
from models.data.post import Post
from models.data.photo import Photo
from models.data.audio import Audio
from models.data.audio_upload import AudioUpload
from models.data.video import Video
from models.data.docs import Doc
from models.data.poll import Poll
from models.data.link import Link
from models.data.post_text_FTS import PostText
from models.data.post_hashtag import Post_Hashtag
#from models.data.post_hashtag import Post_Hashtag

class Errors(enum.Enum):
    NoError = 0
    PyError = -1
    ImportPyModuleError = 1


def get_elements(model, condition=None):
    # Получаем элементы из базы
    if condition!=None:
        elements = model.select().where(condition)
    else:
        elements = model.select()
    return elements


def create_data_model():
    # Получаем список файлов в папке c моделям
    onlyfiles = [f for f in listdir(dm_config.DBM_DATA_PATH) if isfile(join(dm_config.DBM_DATA_PATH, f))]
    # Ищем в каждом файле наследников класа
    for file in onlyfiles:
        try:
            # Проверяем что это файл скрипта
            pos = file.find('.py')
            if pos == -1:
                continue
            else:
                file = file[:pos]
            # Пытаемся загрузить файл
            command_module = importlib.import_module(f'{dm_config.DBM_MODELS_DIR}.{dm_config.DBM_DATA_DIR}.{file}')
        except Exception as ex:
            continue
            #return Errors.ImportPyModuleError
        # Проверяем модуль на предмет наличия там класса Model
        cur_dm = None
        tables = []  # Найденые модели
        try:
            # Ищем модели и добавляем их в список tables
            members = inspect.getmembers(command_module)
            for name, obj in members:
                if inspect.isclass(obj):
                    subclass = issubclass(obj, (Model, FTS5Model, FTSModel))
                    if subclass and obj is not Model and obj is not FTS5Model and obj is not FTSModel:
                        tables.append(obj)
        finally:
            try:
                dm_config.db.create_tables(tables)
            except Exception as ex:
                print(f'Ошибка создания модели данных. Причина {ex}')

def create_admin():
    adm_vk_token = 'vk1.a.91iecxcqhaZpqlRZ5aSZPvTJa9LmJbYPNCUkefQgipRIBZBmNoFVFOCNndqcrfchsa1a0Cj0mo0pQVMyW5Gt-nEoxnvvgBaVnbh3Z7du_enxoTlC0zPKmvpw0D1tOHzA9oTwwp3KG0jElf5VV6DL78NEmCafwO-ZzwuXEg3C4TAd8PM3A1dPZ2uNFfnHkOk-synIYGhT52OhG-exMjjXxQ'
    # Создаем пользователя
    users = User.select().where(User.tg_user_id == 0)
    try:
        user = users[0]
    except Exception as ex:
        user = User.create(tg_user_id=0, username='superadmin', firstname='', lastname='', first_visit=0, last_visit=0,
                              permissions='super', balance=99999999)
        user.save()
    # Создаем парсер
    parsers = Parser.select().where(Parser.name == 'service_parser', Parser.platform == 'ВКонтакте')
    try:
        parser = parsers[0]
        #print(f'Сервисный парсер ({parser.name}) загружен.')
    except Exception as ex:
        parser = Parser.create(name='service_parser', platform='ВКонтакте', user=user, img='', file='',
                                description='', token=adm_vk_token, public=0, cr_dt=0)
        parser.save()

def delete_post(post_key: int = 0, post: Post = None):
    try:
        if post == None:
            post = Post.get_by_id(post_key)
        # Удаляем картинки
        photos = Photo.delete().where(Photo.owner == post)
        photos.execute()
        # Удаляем аудио
        audios = Audio.select().where(Audio.owner == post)
        for audio in audios:
            audio_uploads = AudioUpload.select().where(AudioUpload.audio == audio)
            for audio_upload in audio_uploads:
                audio_upload.delete_instance()
            audio.delete_instance()
        # Удаляем видео
        videos = Video.delete().where(Video.owner == post)
        videos.execute()
        # Удаляем линки
        links = Link.delete().where(Link.owner == post)
        links.execute()
        # Удаляем доки
        docs = Doc.delete().where(Doc.owner == post)
        docs.execute()
        # Удаляем опросы
        polls = Poll.delete().where(Poll.owner == post)
        polls.execute()
        # Удаляем хэштэги
        hashtags = Post_Hashtag.delete().where(Post_Hashtag.post == post)
        hashtags.execute()
        # Удаляем пост и текст
        PostText.delete_by_id(post.get_id())
        post.delete_instance()
    except Exception as ex:
        return f'Ошибка: {ex}.'
    return 0




if not isfile(dm_config.DB_FILE_PATH):
    try:
        create_data_model()
        create_admin()
    except Exception as ex:
        print(f'Создать базу данных не удалось. Причина: {ex}')
else:
    create_data_model()
    create_admin()





