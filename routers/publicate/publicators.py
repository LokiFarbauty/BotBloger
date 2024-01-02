'''Модуль отвечает за публикацию сообщений в телеграмме'''

import asyncio
import enum
from math import ceil
from aiogram import types

# models
from models.data.publicator import Publicator, PublicatorStates, PublicatorModes
from models.data.channel import Channel
from models.data.post import Post
from models.data.video import Video
from models.data.link import Link
from models.data.audio import Audio
from models.data.docs import Doc
from models.data.poll import Poll
from models.data.photo import Photo
from models.data.bot import Bot as BotModel
from models.data.post_text_FTS import PostText

# routers
from routers.bots.telegram.bots import get_BotExt, BotStatus
from routers.logers import publicators_loger
from routers.publicate.telegraph_tools import put_post_to_telegraph


# class TGPublicator():
#     def __init__(self, db_key: int, task: asyncio.Task, state: int):
#         self.task = task
#         self.db_key = db_key
#         self.state = state
#
#     @classmethod
#     def public_post(cls, tg_channel_id: int, post_key: int):
#         '''Публикует пост из дазы в телеграм-канал'''
#         pass

current_publicators = [] # Работающие в текущий момент публикаторы

class PublicateErrors(enum.Enum):
    NoError = 'опубликовано без ошибок'
    BotError = 'ошибка бота'
    MatError = 'в посте обнаружены запрещенные слова, он не опубликован'
    TGPHError = 'не удалось опубликовать пост в Телеграф'
    OtherError = 'неизвестная ошибка, смотрите логи'

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


def check_mat_in_text(text: str):
    res = False
    mat_words = ['хуй', 'хуёв', 'хуев', 'пизд', 'Пизд', ' бля ', 'блять', ' бляд', 'ебать', 'ебаный', 'ебанут', 'ёбаный', 'русня', 'ебал', 'путлер',
                 'пидор', ' гей ', ' геи ', 'лесби', 'русак', ' хач', ' чурка ', ' жид ', ' жиды ', ' жидов', ' пыня ', ' навальный ', 'свинорус', 'Фриске', 'Серебряков',
                 'Яровой', ' Христос', ' Аллах', ' христос', ' алах', ' аллах']
    mat_words = ['русня',  'путлер', 'рашк', 'Рашк', 'рашке', 'рашки', 'рашку', 'рашке',
                 ' гей ', ' геи ', 'лесби', 'русак', ' хач ', ' чурка ', ' жид ', ' жиды ', ' жидов', ' пыня ',
                 ' навальный ', 'свинорус', 'Фриске', 'Серебряков',
                 'Яровой', ' Христос', ' Аллах', ' христос', ' алах', ' аллах ']
    for word in mat_words:
        if text.find(word)!=-1:
            res = True
            return res
        if text.find(word.upper())!=-1:
            res = True
            return res
    return res

def split_post_text(post_text, max_len=1020, t_range=200, first=False):
    text_parts = ceil(len(post_text) / max_len)
    text_posts = []
    before=True
    l_sep = 0
    if len(post_text)<max_len:
        text_posts.append(post_text)
        return text_posts
    for i in range(1, text_parts+1, 1):
        #start=i * len(post_text) - t_range
        #end=i * len(post_text)
        start=i * max_len - t_range
        end=i * max_len
        sep = post_text.find('<a href', start, end)
        if sep == -1:
            sep = post_text.find('https://', start, end)
        if sep == -1:
            before = False
            sep = post_text.find('.', start, end)
        if sep == -1:
            sep = post_text.find(',', start, end)
        if sep == -1:
            sep = post_text.find(' ', start, end)
        if sep == -1:
            sep = (i * max_len)
        if before:
            new_str = post_text[l_sep:sep - 1]
        else:
            new_str=post_text[l_sep:sep+1]
        new_str=new_str.strip()
        text_posts.append(new_str)
        l_sep = sep+1
        if first:
            break
    if before:
        l_sep=l_sep-1
    remains=post_text[l_sep:]
    remains=remains.strip()
    if remains!='':
        text_posts.append(remains)
    return text_posts

async def public_post_to_channel(publicator: Publicator, post: Post):
    try:
        post_key = post.get_id()
        # Получаем id канала
        channel_tg_id = publicator.channel.channel_tg_id
        # Получаем бота
        bot_obj = await get_BotExt(publicator.bot)
        if bot_obj == None:
            publicators_loger.error(
                f'Попытка публикации через неизвестного бота. Публикатор: {publicator.get_id()}. Пост: {post.get_id()}. Публикатор будет остановлен.')
            return PublicateErrors.BotError
        if bot_obj.status != BotStatus.InWork:
            publicators_loger.error(
                f'Попытка публикации через неизвестного бота. Публикатор: {publicator.get_id()}. Пост: {post.get_id()}. Публикатор будет остановлен.')
            return PublicateErrors.BotError
        # Проверяем пост на наличие мата
        post_index = PostText.get_by_id(post_key)
        post_text = post_index.text
        if publicator.criterion.check_mat == 1:
            check_mat = check_mat_in_text(post_text)
            if check_mat:
                return PublicateErrors.MatError
        # Получаем картинки
        imgs_mlds = Photo.select().where(Photo.owner==post)
        img_urls = []
        for img_mld in imgs_mlds:
            img_urls.append(img_mld.url)
        if len(img_urls)>10:
            img_urls = img_urls[:9]
        # Добавляем в текст линки и ссылки на видео
        videos = Video.select().where(Video.owner==post)
        for video in videos:
            post_text = f'{post_text}\n<a href="{video.url}">{video.title}</a>'
        links = Link.select().where(Link.owner == post)
        for link in links:
            post_text = f'{post_text}\n<a href="{link.url}">{link.title}</a>'
        # Проверяем длинну текста
        post_text_len = len(post_text)
        if (post_text_len > PostTextlen.Short.value):
            # Текст длинный
            state = 'Размещение длинного текста'
            # Удаляем ссылки из текста
            url_pos = post_text.find('<a href=')
            if url_pos != -1:
                post_text = post_text[:url_pos-1]
            # Формируем страничку в телеграфе
            author_caption = publicator.author_caption
            tg_url = await put_post_to_telegraph(post, telegraph_token=publicator.telegraph_token,
                                                 author_caption=author_caption, author_name=publicator.author_name,
                                                 author_url=publicator.author_url)
            if tg_url == '':
                # Создать страничку в телеграфе не удалось
                return PublicateErrors.TGPHError
            else:
                post_text = f'{post_text}\n<b><a href="{tg_url}">Показать полностью</a></b>'
                post.telegraph_url = tg_url
                post.save()
            # Получаем превью текста
            post_text_lst = split_post_text(post_text, max_len=1000, first=True)
            post_text_preview = post_text_lst[0]
            # Готовим картинку (при наличии)
            if len(img_urls) == 0:
                await bot_obj.send_message(chat_id=channel_tg_id, text=post_text_preview, parse_mode='HTML',
                                       disable_web_page_preview=False)
            elif len(img_urls) == 1:
                await bot_obj.send_photo(chat_id=channel_tg_id, photo=img_urls[0], caption=post_text_preview, parse_mode='HTML')
            elif len(img_urls) > 1:
                media = []
                first = True
                for el in img_urls:
                    if first:
                        media.append(types.InputMediaPhoto(media=el, caption=post_text_preview, parse_mode='HTML'))
                    else:
                        first = False
                        media.append(types.InputMediaPhoto(media=el))
                await bot_obj.send_media_group(chat_id=channel_tg_id, media=media)  # Отправка фото
        elif (post_text_len <= PostTextlen.Short.value):
            # Текст короткий
            state = 'Размещение короткого текста'
            # Добовляем авторскую подпись
            try:
                if publicator.author_caption != None:
                    sum_len = post_text_len + len(publicator.author_caption)
                    if sum_len < 1023:
                        post_text = f'{post_text}\n{publicator.author_caption}'
            except:
                pass
            # Готовим картинку (при наличии)
            if len(img_urls) == 0 and post_text_len > 0:
                await bot_obj.send_message(chat_id=channel_tg_id, text=post_text, parse_mode='HTML',
                                       disable_web_page_preview=False)
            elif len(img_urls) == 1:
                await bot_obj.send_photo(chat_id=channel_tg_id, photo=img_urls[0], caption=post_text, parse_mode='HTML')
            elif len(img_urls) > 1:
                media = []
                first = True
                for el in img_urls:
                    if first:
                        media.append(types.InputMediaPhoto(media=el, caption=post_text, parse_mode='HTML'))
                    else:
                        first = False
                        media.append(types.InputMediaPhoto(media=el))
                await bot_obj.send_media_group(chat_id=channel_tg_id, media=media)  # Отправка фото
        else:
            pass
        # Выкладываем документы, аудио, опросы
        # Получаем и выкладываем документы
        state = 'Размещение документов'
        doc_mlds = Doc.select().where(Doc.owner == post)
        doc_urls = []
        for doc_mld in doc_mlds:
            doc_urls.append(doc_mld.url)
        if len(doc_urls) > 10:
            doc_urls = doc_urls[:9]
        if len(doc_urls) == 1:
            await bot_obj.send_document(chat_id=channel_tg_id, document=doc_urls[0], caption='👆', parse_mode='HTML')
        elif len(doc_urls) > 1:
            media = []
            first = True
            for el in doc_urls:
                if first:
                    media.append(types.InputMediaDocument(media=el, caption='👆', parse_mode='HTML'))
                else:
                    first = False
                    media.append(types.InputMediaDocument(media=el))
            await bot_obj.send_media_group(chat_id=channel_tg_id, media=media)  # Отправка документов
        # Получаем и выкладываем аудио
        state = 'Размещение аудио'
        audio_mlds = Audio.select().where(Audio.owner == post)
        audio_urls = []
        audio_titles = []
        audio_artists = []
        for audio_mld in audio_mlds:
            if audio_mld.url != '':
                audio_urls.append(audio_mld.url)
                audio_titles.append(audio_mld.title)
                audio_artists.append(audio_mld.artist)
        if len(audio_urls) > 10:
            audio_urls = audio_urls[:9]
        if len(audio_urls) == 1:
            await bot_obj.send_audio(chat_id=channel_tg_id, audio=audio_urls[0], performer=audio_artists[0],
                                     title=audio_titles[0], parse_mode='HTML')
        elif len(audio_urls) > 1:
            media = []
            for i, el in enumerate(audio_urls, 0):
                media.append(types.InputMediaAudio(media=el, performer=audio_artists[i], title=audio_titles[i]))
            await bot_obj.send_media_group(chat_id=channel_tg_id, media=media)  # Отправка документов
        # Получаем и выкладываем опросы
        state = 'Размещение опроса'
        poll_mlds = Poll.select().where(Poll.owner == post)
        for poll_mld in poll_mlds:
            options = poll_mld.answers.split('||')
            await bot_obj.send_poll(chat_id=channel_tg_id, question=poll_mld.question, options=options)  # Отправка опросов
        #
        return PublicateErrors.NoError
    except Exception as ex:
        publicators_loger.error(f'Ошибка публикатора {publicator.get_id()}(пост: {post.get_id()}, стадия: "{state}"): {ex}')
        return PublicateErrors.OtherError


async def publicating(publicator: Publicator):
    '''Поток публикатора, в котором он периодически получает из базы посты и публикует их в канал'''
    # Получаем посты
    posts=[]
    parse_program_key = publicator.parse_program.get_id()
    parse_task_key = publicator.parse_task.get_id()
    last_post_id = publicator.last_post_id
    if publicator.mode == PublicatorModes.New:
        # Публикуем новые посты
        # Получаем поcты предназначенные к публикации
        if parse_program_key==0 or parse_program_key==None:
            condition = Post.post_id > last_post_id | Post.parse_task == parse_task_key
        else:
            condition = Post.post_id > last_post_id | Post.parse_program == parse_task_key
        posts = Post.select().where(condition).order_by(Post.post_id.asc())
    for post in posts:
        res = await public_post_to_channel(publicator, post)
        if res == PublicateErrors.BotError:
            # Критическая ошибка публикации, останавливаем публикатор
            publicator.state = PublicatorStates.Stopped_Error
            publicator.save()
            return


    # Спим
    if publicator.period>0:
        await asyncio.sleep(publicator.period)
    else:
        return

async def init_current_publicators():
    '''Инициализация публикаторов
    Загрузка данных из базы и запуск потоков публикаторов'''
    # Загружаем данные из базы
    publicators_mld = Publicator.select().where(Publicator.state==PublicatorStates.Working.value)
    for publicator_mld in publicators_mld:
        # Получаем канал
        channel = Channel.get_by_id(publicator_mld.channel)
        # Создаем задачу
        publicator_task = asyncio.create_task(publicating(period=publicator_mld.period,
                                                          tg_channel_id=channel,
                                                          mode=publicator_mld.mode,
                                                          parse_task_key=publicator_mld.parse_task,
                                                          parse_program_key=publicator_mld.parse_program,
                                                          last_post_id = publicator_mld.last_post_id), name=publicator_mld.name)
        #publicator_obj = TGPublicator(db_key=publicator_mld.get_id(), task=publicator_task, state=publicator_mld.state)
        #current_publicators.append(publicator_obj)



