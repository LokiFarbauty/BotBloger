'''Модуль отвечает за публикацию сообщений в телеграмме'''

import asyncio
from math import ceil
from aiogram import types
from datetime import datetime
from peewee import fn
import yt_dlp
import main_config
import os



# models
from models.data.publicator import Publicator, PublicatorStates, PublicatorModes
from models.data.channel import Channel
from models.data.post import Post, ModerateStates
from models.data.hashtag import Hashtag
from models.data.post_hashtag import Post_Hashtag
from models.data.video import Video
from models.data.link import Link
from models.data.audio import Audio
from models.data.docs import Doc
from models.data.poll import Poll
from models.data.photo import Photo
from models.data.ol_twin_channel import TwinChannel
from models.data.bot import Bot as BotModel
from models.data.post_text_FTS import PostText
from models.data_model import delete_post

# routers
from routers.bots.telegram.bots import get_BotExt, BotStatus
from routers.logers import publicators_loger, app_loger
from routers.publicate.telegraph_tools import put_post_to_telegraph
from routers.parsing.analyzer import check_text
from routers.publicate.video_tools import download_and_compress_video
from routers.translation.translation import translate_text
from routers.publicate.enums import *


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

current_publicators_process = [] # Работающие в текущий момент публикаторы




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

def get_publicator_process_state(name: str):
    for el in current_publicators_process:
        el_name = el.get_name()
        if el_name == name:
            task_process = el
            if task_process.done():
                return PBTaskStatus.Done
            if task_process.cancelled():
                return PBTaskStatus.Cancelled
            return PBTaskStatus.Active
    return PBTaskStatus.NotFound

def get_publicator_process(name: str):
    for el in current_publicators_process:
        el_name = el.get_name()
        if el_name == name:
            return el
    return None

def stop_publicator_process(name: str, remove_process = True):
    for el in current_publicators_process:
        el_name = el.get_name()
        if el_name == name:
            try:
                el.cancel()
                if remove_process:
                    current_publicators_process.remove(el)
                # Меняем статус в базе
                publ = Publicator.get_publicator(name=name)
                if publ != None:
                    publ.state = PBTaskStatus.Cancelled.value
                    publ.save()
            except Exception as ex:
                return ex
    return PBTaskStatus.Cancelled

def start_publicator_process(publicator: Publicator):
    # Ищем была ли задача и удаляем ее из списка
    task_process = get_publicator_process(publicator.name)
    if task_process == None:
        # Запускаем процесс
        publicator_task = asyncio.create_task(publicating(publicator), name=publicator.name)
        current_publicators_process.append(publicator_task)
        return f'Публикатор "{publicator.name}" запущен.'
    else:
        task_status = get_publicator_process_state(publicator.name)
        if task_status == PBTaskStatus.Active:
            return f'Публикатор "{publicator.name}" уже запущен.'
        else:
            current_publicators_process.remove(task_process)
            publicator_task = asyncio.create_task(publicating(publicator), name=publicator.name)
            current_publicators_process.append(publicator_task)
            return f'Публикатор "{publicator.name}" запущен.'



async def public_post_to_channel(publicator: Publicator, post: Post, save_last_post_id = False, twin_channel = None, def_post_lang = 'ru'):
    # Опубликовать пост в канале
    try:
        state = 'Подготовка к публикации'
        post_key = post.get_id()
        # Получаем id канала
        if twin_channel != None:
            channel_tg_id = twin_channel.channel_tg_id
        else:
            channel_tg_id = publicator.channel.channel_tg_id
        # Получаем бота
        bot_obj = await get_BotExt(publicator.bot)
        if bot_obj == None:
            publicators_loger.error(
                f'Попытка публикации через неизвестного бота. Публикатор: {publicator.get_id()}. Пост: {post.get_id()}. Публикатор будет остановлен.')
            return PublicateErrors.BotError
        if bot_obj.status != BotStatus.InWork:
            publicators_loger.error(
                f'Попытка публикации через неработающего бота. Публикатор: {publicator.get_id()}. Пост: {post.get_id()}. Публикатор будет остановлен.')
            return PublicateErrors.BotError
        # Проверяем пост на наличие мата
        post_index = PostText.get_by_id(post.text)
        post_text = post_index.text
        # Переводим текст
        try:
            if post.translation != 'ru':
                post_text = translate_text(post_text, to_language=post.translation)
        except Exception as ex:
            publicators_loger.warning(f'Не удалось перевести текст {post_index} на язык {post.translation}. Ошибка: {ex}')
        # if publicator.criterion.check_mat == 1:
        #     check_mat = check_mat_in_text(post_text)
        #     if check_mat:
        #         return PublicateErrors.MatError
        # Получаем картинки
        imgs_mlds = Photo.select().where(Photo.owner==post)
        img_urls = []
        img_caption = ''
        for img_mld in imgs_mlds:
            img_urls.append(img_mld.url)
            if img_caption=='' and img_mld.caption != '':
                img_caption = img_mld.caption
                if post.translation != 'ru':
                    img_caption = translate_text(img_caption, to_language=post.translation)
        if len(img_urls)>10:
            img_urls = img_urls[:9]
        # Добавляем в текст линки и ссылки на видео
        videos = Video.select().where(Video.owner==post)
        video_files = []
        for video in videos:
            try:
                # Проверяем наличие файла видео
                try:
                    filename = ''
                    if os.path.exists(video.file):
                        filename = video.file
                except:
                    filename = ''
                # Если его нет скачиваем видео
                if filename == '':
                    filename = await download_and_compress_video(video.url,
                                                       output_directory=main_config.DOWNLOADS_PATH,
                                                       target_size=51000000,
                                                       max_duration=1800)
                if filename != '':
                    # Выкладываем видео
                    video_files.append(filename)
                    video.file = filename
                    try:
                        video.save()
                    except:
                        pass
                else:
                    raise ValueError("Выкладываем видео ссылкой")
                #
            except:
                videotitle = video.title
                if post.translation != 'ru':
                    videotitle = translate_text(videotitle, to_language=post.translation)
                post_text = f'{post_text}\n<a href="{video.url}">{videotitle}</a>'
        links = Link.select().where(Link.owner == post)
        for link in links:
            linktitle=link.title
            if post.translation != 'ru':
                linktitle = translate_text(linktitle, to_language=post.translation)
            post_text = f'{post_text}\n<a href="{link.url}">{linktitle}</a>'
        # Если нет текста, но есть картинка, берем текст из описания картинки
        if post_text == '':
            post_text = img_caption
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
            # Ищем создавалась ли страница в телеграфе ранее
            tg_url = post.telegraph_url
            if tg_url == '' or tg_url == None or twin_channel != None:
                author_caption = publicator.author_caption
                if post.translation != 'ru':
                    author_caption = translate_text(author_caption, to_language=post.translation)
                tg_url = await put_post_to_telegraph(post, telegraph_token=publicator.telegraph_token,
                                                     author_caption=author_caption, author_name=publicator.author_name,
                                                     author_url=publicator.author_url)
            # Получаем превью текста
            post_text_lst = split_post_text(post_text, max_len=1000, first=True)
            post_text_preview = post_text_lst[0]
            if tg_url == '':
                # Создать страничку в телеграфе не удалось
                return PublicateErrors.TGPHError
            else:
                spoiler_text = "Показать полностью"
                if post.translation != 'ru':
                    spoiler_text = translate_text(spoiler_text, to_language=post.translation)
                post_text_preview = f'{post_text_preview}\n<b><a href="{tg_url}">{spoiler_text}</a></b>'
                post.telegraph_url = tg_url
                post.translation = def_post_lang
                post.save()
            # Готовим картинку и видео (при наличии)
            if len(img_urls) == 0 and len(video_files) == 0 :
                try:
                    await bot_obj.send_message(chat_id=channel_tg_id, text=post_text_preview, parse_mode='HTML',
                                       disable_web_page_preview=True)
                except:
                    pass
            elif len(img_urls) == 1 and len(video_files) == 1:
                media = []
                media.append(types.InputMediaPhoto(media=img_urls[0], caption=post_text_preview, parse_mode='HTML'))
                media.append(types.InputMediaVideo(media=types.FSInputFile(video_files[0]), supports_streaming=True, parse_mode='HTML'))
                try:
                    await bot_obj.send_media_group_ex(chat_id=channel_tg_id, media=media)  # Отправка фото
                except:
                    pass
            elif len(img_urls) == 1 or len(video_files) == 1:
                if len(img_urls) == 1:
                    try:
                        await bot_obj.send_photo(chat_id=channel_tg_id, photo=img_urls[0], caption=post_text_preview, parse_mode='HTML')
                    except:
                        pass
                if len(video_files) == 1:
                    try:
                        #with open(video_files[0], 'rb') as video:
                        video = types.FSInputFile(video_files[0])
                        await bot_obj.send_video(chat_id=channel_tg_id, video=video, caption=post_text_preview, parse_mode='HTML', supports_streaming=True)
                    except:
                        pass
            elif len(img_urls) > 1 or len(video_files) > 1:
                media = []
                first = True
                for el in img_urls:
                    if first:
                        media.append(types.InputMediaPhoto(media=el, caption=post_text_preview, parse_mode='HTML'))
                        first = False
                    else:
                        media.append(types.InputMediaPhoto(media=el))
                for video in video_files:
                    if first:
                        media.append(types.InputMediaVideo(media=types.FSInputFile(video), caption=post_text_preview, supports_streaming=True, parse_mode='HTML'))
                        first = False
                    else:
                        media.append(types.InputMediaVideo(media=types.FSInputFile(video), supports_streaming=True))
                try:
                    media = media[:9]
                except:
                    pass
                try:
                    await bot_obj.send_media_group_ex(chat_id=channel_tg_id, media=media)  # Отправка фото
                except:
                    pass
        elif (post_text_len <= PostTextlen.Short.value):
            # Текст короткий
            state = 'Размещение короткого текста'
            # Добовляем авторскую подпись
            try:
                if publicator.author_caption != None:
                    author_caption = publicator.author_caption
                    if post.translation != 'ru':
                        author_caption = translate_text(author_caption, to_language=post.translation)
                    sum_len = post_text_len + len(author_caption)
                    if sum_len < 1023:
                        #post_text = f'{post_text}\n{publicator.author_caption}'
                        pass
            except:
                pass
            # Готовим картинку (при наличии)
            if len(img_urls) == 0 and len(video_files) == 0 and post_text_len > 0:
                try:
                    await bot_obj.send_message(chat_id=channel_tg_id, text=post_text, parse_mode='HTML',
                                       disable_web_page_preview=False)
                except:
                    pass
            elif len(img_urls) == 1 and len(video_files) == 1:
                media = []
                media.append(types.InputMediaPhoto(media=img_urls[0], caption=post_text, parse_mode='HTML'))
                media.append(types.InputMediaVideo(media=types.FSInputFile(video_files[0]), supports_streaming=True, parse_mode='HTML'))
                try:
                    await bot_obj.send_media_group_ex(chat_id=channel_tg_id, media=media)  # Отправка фото
                except:
                    pass
            elif len(img_urls) == 1 or len(video_files) == 1:
                if len(img_urls) == 1:
                    try:
                        await bot_obj.send_photo(chat_id=channel_tg_id, photo=img_urls[0], caption=post_text, parse_mode='HTML')
                    except:
                        pass
                if len(video_files) == 1:
                    try:
                        video = types.FSInputFile(video_files[0])
                        await bot_obj.send_video(chat_id=channel_tg_id, video=video, caption=post_text,
                                                 parse_mode='HTML', supports_streaming=True)
                    except Exception as ex:
                        pass
            elif len(img_urls) > 1 or len(video_files) > 1:
                media = []
                first = True
                for el in img_urls:
                    if first:
                        media.append(types.InputMediaPhoto(media=el, caption=post_text, parse_mode='HTML'))
                        first = False
                    else:
                        media.append(types.InputMediaPhoto(media=el))
                for video in video_files:
                    if first:
                        media.append(types.InputMediaVideo(media=types.FSInputFile(video), caption=post_text, supports_streaming=True, parse_mode='HTML'))
                        first = False
                    else:
                        media.append(types.InputMediaVideo(media=types.FSInputFile(video), supports_streaming=True))
                try:
                    media = media[:9]
                except:
                    pass
                try:
                    await bot_obj.send_media_group_ex(chat_id=channel_tg_id, media=media)  # Отправка фото
                except Exception as ex:
                    pass
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
            try:
                await bot_obj.send_document(chat_id=channel_tg_id, document=doc_urls[0], caption='👆', parse_mode='HTML')
            except:
                try:
                    file_spoiler = 'Файл'
                    if post.translation != 'ru':
                        file_spoiler = translate_text(file_spoiler, to_language=post.translation)
                    await bot_obj.send_message(chat_id=channel_tg_id, text=f'<a href="{doc_urls[0]}">{file_spoiler}</a>', parse_mode='HTML')
                except Exception as ex:
                    publicators_loger.error(f'Не получилось выложить ссылку на документ "{doc_urls[0]}". Ошибка: {ex}')
        elif len(doc_urls) > 1:
            media = []
            first = True
            docs_str = ''
            for el in doc_urls:
                if first:
                    media.append(types.InputMediaDocument(media=el, caption='👆', parse_mode='HTML'))
                else:
                    first = False
                    media.append(types.InputMediaDocument(media=el))
                file_spoiler = 'Файл'
                if post.translation != 'ru':
                    file_spoiler = translate_text(file_spoiler, to_language=post.translation)
                docs_str = f'{docs_str}<a href="{el}">{file_spoiler}</a>\n'
            try:
                await bot_obj.send_media_group_ex(chat_id=channel_tg_id, media=media)  # Отправка документов
            except:
                try:
                    await bot_obj.send_message(chat_id=channel_tg_id, text=docs_str, parse_mode='HTML')
                except Exception as ex:
                    publicators_loger.error(f'Не получилось выложить ссылку на документ "{docs_str}". Ошибка: {ex}')
        # Получаем и выкладываем аудио
        state = 'Размещение аудио'
        audio_mlds = Audio.select().where(Audio.owner == post)
        audio_urls = []
        audio_titles = []
        audio_artists = []
        for audio_mld in audio_mlds:
            if audio_mld.url != '':
                audio_urls.append(audio_mld.url)
                audio_mld_title = audio_mld.title
                if post.translation != 'ru':
                    audio_mld_title = translate_text(audio_mld_title, to_language=post.translation)
                audio_titles.append(audio_mld_title)
                audio_mld_artist = audio_mld.artist
                if post.translation != 'ru':
                    audio_mld_artist = translate_text(audio_mld_artist, to_language=post.translation)
                audio_artists.append(audio_mld_artist)
        if len(audio_urls) > 10:
            audio_urls = audio_urls[:9]
        if len(audio_urls) == 1:
            #await bot_obj.send_audio(chat_id=channel_tg_id, audio=audio_urls[0], performer=audio_artists[0], title=audio_titles[0])
            sf = types.URLInputFile(url=audio_urls[0], filename=f'{audio_artists[0]} - {audio_titles[0]}.mp3')
            try:
                await bot_obj.send_document(chat_id=channel_tg_id, document=sf)
            except:
                pass
        elif len(audio_urls) > 1:
            media = []
            for i, el in enumerate(audio_urls, 0):
                media.append(types.InputMediaAudio(media=el, performer=audio_artists[i], title=audio_titles[i]))
            try:
                await bot_obj.send_media_group_ex(chat_id=channel_tg_id, media=media)  # Отправка audio
            except:
                pass
        # Получаем и выкладываем опросы
        state = 'Размещение опроса'
        poll_mlds = Poll.select().where(Poll.owner == post)
        for poll_mld in poll_mlds:
            poll_mld_answers = poll_mld.answers
            if post.translation != 'ru':
                poll_mld_answers = translate_text(poll_mld_answers, to_language=post.translation)
            options = poll_mld_answers.split('||')
            try:
                poll_mld_question = poll_mld.question
                if post.translation != 'ru':
                    poll_mld_question = translate_text(poll_mld_question, to_language=post.translation)
                await bot_obj.send_poll(chat_id=channel_tg_id, question=poll_mld_question, options=options)  # Отправка опросов
            except:
                pass
        # Сохраняем статус публикатора
        if save_last_post_id:
            publicator.last_post_id = post.post_id
            publicator.save()
        post.published = 1
        dt = datetime.now()
        cr_dt = dt.replace(microsecond=0).timestamp()
        post.last_published_dt = cr_dt
        post.translation = def_post_lang
        post.save()
        #
        return PublicateErrors.NoError
    except Exception as ex:
        publicators_loger.error(f'Ошибка публикатора {publicator.get_id()}(пост: {post.get_id()}, стадия: "{state}"): {ex}')
        return PublicateErrors.OtherError

async def get_hashtags_posts(hts: str, old_posts=None):
    try:
        hashtags = hts.replace(', ', ',')
        hashtags = hashtags.split(',')
        hashtags = [x.lower() for x in hashtags]
        hashtags = [x.strip() for x in hashtags]
        # Получаем посты с хэштэгами
        ht_cond = None
        for ht in hashtags:
            if ht_cond != None:
                ht_cond = ((ht_cond) | (Post_Hashtag.hashtag.value == ht))
            else:
                ht_cond = (Post_Hashtag.hashtag.value == ht)
        if old_posts is None or type(old_posts) is list:
            posts = Post.select().join(Post_Hashtag).join(Hashtag).where(ht_cond)
        else:
            posts = old_posts.select().join(Post_Hashtag).join(Hashtag).where(ht_cond)
        # for post in posts:
        #     print(post.get_id())
        return posts
    except Exception as ex:
        return []

async def get_posts(condition, old_posts=None, order=Post.post_id.asc()):
    try:
        if old_posts is None or type(old_posts) is list:
            posts = Post.select().where(condition).order_by(order)
        else:
            posts = old_posts.select().where(condition).order_by(order)
    except:
        posts = []
    return posts

async def get_random_posts(condition, old_posts=None):
    try:
        #posts_num = old_posts.select().where(condition).count()
        if old_posts is None or type(old_posts) is list:
            posts = Post.select().where(condition).order_by(fn.Random()).limit(1)
        else:
            posts = old_posts.select().where(condition).order_by(fn.Random()).limit(1)
    except Exception as ex:
        posts = []
    return posts


async def publicating(par_publicator: Publicator, debug=False):
    '''Поток публикатора, в котором он периодически получает из базы посты и публикует их в канал'''
    try:
        if debug: publicators_loger.info(f'Публикатор {par_publicator.name} готов к старту. Задержка {par_publicator.start_delay} сек.')
        await asyncio.sleep(int(par_publicator.start_delay))
        if debug: publicators_loger.info(f'Публикатор {par_publicator.name} запущен.')
    except:
        publicators_loger.error(f'Задержка публикатора {par_publicator.name} задана не правильно.')
    while True:
        try:
            # Проверяем что публикатор еще существует
            publicator = Publicator.get_publicator(key=par_publicator.get_id())
            if publicator == None:
                return
            # Спим 5 секунд
            await asyncio.sleep(10)
            # Проверяем время публикации
            start_public_hour = publicator.start_public_hour
            end_public_hour = publicator.end_public_hour
            cur_time = datetime.now().time().hour
            period = publicator.period
            if debug: publicators_loger.info(f'Публикатор {publicator.name}. Запущен новый цикл проверки. Текущий час: {cur_time}. Границы времени публикации от {start_public_hour} до {end_public_hour}.')
            if cur_time >= start_public_hour and cur_time <= end_public_hour:
                # Обновляем статус
                publicator.state = PublicatorStates.Working.value
                publicator.save()
                if debug: publicators_loger.info(
                    f'Публикатор {publicator.name}. Время публикации. Текущий час: {cur_time}. Период задержки {period} сек ({period/60/60} часа).')
                # Получаем посты
                posts=[]
                try:
                    parse_program_key = publicator.parse_program.get_id()
                except:
                    parse_program_key = 0
                try:
                    parse_task_key = publicator.parse_task.get_id()
                except:
                    parse_task_key = 0
                last_post_id = publicator.last_post_id
                # Определяем критериии для публикации -
                #  хэштег (остальное не поддерживается), ключевое слово или фраза, проверка на запрещенные слова (100 попыток), очистка слов в тексте,
                # длинна текста и даты
                sub_condition = 1
                # Хэштэги
                hts = publicator.criterion.hashtags
                if hts != None and hts != '':
                    posts = await get_hashtags_posts(hts, posts)
                # Даты
                start_date = publicator.criterion.post_start_date
                if start_date != None and start_date != 0:
                    sub_condition = ((sub_condition) & (Post.dt > start_date))
                end_date = publicator.criterion.post_end_date
                if end_date != None and end_date != 0:
                    sub_condition = ((sub_condition) & (Post.dt < end_date))
                # Рейтинг
                min_rate = publicator.criterion.min_rate
                if min_rate > 0:
                    sub_condition = ((sub_condition) & (Post.rate >= min_rate))
                # Длинна текста
                max_text_len = publicator.criterion.post_max_text_length
                if max_text_len != None and max_text_len != 0:
                    sub_condition = ((sub_condition) & (Post.text_len < max_text_len))
                min_text_len = publicator.criterion.post_min_text_length
                if min_text_len != None and min_text_len != 0:
                    sub_condition = ((sub_condition) & (Post.text_len > min_text_len))
                # Получаем посты для публикации
                if publicator.mode == PublicatorModes.New.value:
                    # Публикуем новые посты
                    # Получаем поcты предназначенные к публикации
                    if parse_program_key==0 or parse_program_key==None:
                        condition = ((sub_condition) & (Post.post_id > last_post_id) & (Post.parse_task == parse_task_key))
                    else:
                        condition = ((sub_condition) & (Post.post_id > last_post_id) & (Post.parse_program == parse_program_key))
                    posts = await get_posts(condition, posts)
                elif publicator.mode == PublicatorModes.Single.value:
                    if parse_program_key==0 or parse_program_key==None:
                        condition = ((sub_condition) & (Post.parse_task == parse_task_key))
                    else:
                        condition = ((sub_condition) & (Post.parse_program == parse_program_key))
                    posts = await get_random_posts(condition, posts)
                    period = 0
                elif publicator.mode == PublicatorModes.Period.value:
                    if parse_program_key==0 or parse_program_key==None:
                        condition = ((sub_condition) & (Post.parse_task == parse_task_key))
                    else:
                        condition = ((sub_condition) & (Post.parse_program == parse_program_key))
                    posts = await get_random_posts(condition, posts)
                elif publicator.mode == PublicatorModes.Marketing.value:
                    pass
                elif publicator.mode == PublicatorModes.Premoderate.value:
                    if parse_program_key == 0 or parse_program_key == None:
                        condition = ((sub_condition) & (Post.moderate == ModerateStates.ToPublish.value) & (
                                    Post.parse_task == parse_task_key))
                    else:
                        condition = ((sub_condition) & (Post.moderate == ModerateStates.ToPublish.value) & (
                                    Post.parse_program == parse_program_key))
                    posts = await get_posts(condition, posts, order=Post.dt.asc())
                # Размещаем посты
                if debug: publicators_loger.info(
                    f'Публикатор {publicator.name}. Условие выборки поста сформировано. Текущий час: {cur_time}. Период задержки {period} сек ({period / 60 / 60} часа).')
                for post in posts:
                    try:
                        #print(post.get_id())
                        if debug: publicators_loger.info(
                            f'Публикатор {publicator.name}. Начало просмотра выбраных постов. Текущий час: {cur_time}. Период задержки {period} сек ({period / 60 / 60} часа).')
                        post_text_key = post.text
                        post_text_mld = PostText.get_by_id(post_text_key)
                        post_text = post_text_mld.text
                        # Проверяем на запрещенные слова, если они есть то кидаем цикл на новый виток
                        if publicator.criterion.forbidden_words != None and publicator.criterion.forbidden_words != '':
                            if not check_text(post_text, publicator.criterion.forbidden_words):
                                if debug: publicators_loger.info(
                                    f'Публикатор {publicator.name}. Пост {post.get_id()} не подходит - запрещенные слова. Текущий час: {cur_time}. Период задержки {period} сек ({period / 60 / 60} часа).')
                                continue
                        # Проверяем текст на мат
                        if publicator.criterion.check_mat != None and publicator.criterion.check_mat != 0:
                            if check_mat_in_text(post_text):
                                if debug: publicators_loger.info(
                                    f'Публикатор {publicator.name}. Пост {post.get_id()} не подходит - мат. Текущий час: {cur_time}. Период задержки {period} сек ({period / 60 / 60} часа).')
                                continue
                        if debug: publicators_loger.info(
                            f'Публикатор {publicator.name}. Публикуем пост {post.get_id()}. Текущий час: {cur_time}. Период задержки {period} сек ({period / 60 / 60} часа).')
                        res = await public_post_to_channel(publicator, post)
                        if res == PublicateErrors.BotError:
                            # Критическая ошибка публикации, останавливаем публикатор
                            publicator.state = PublicatorStates.Stopped_Error.value
                            publicator.save()
                            if debug: publicators_loger.info(
                                f'Публикатор {publicator.name}. Пост {post.get_id()} - критическая ошибка бота, публикатор остановлен. Текущий час: {cur_time}. Период задержки {period} сек ({period / 60 / 60} часа).')
                            return
                        # Публикуем в дублирующие каналы
                        twins_channels = TwinChannel.get_twins_channels(publicator.channel)
                        for twin_channel in twins_channels:
                            try:
                                # Выбираем язык
                                post.translation = twin_channel.language
                                # Размещаем
                                res = await public_post_to_channel(publicator, post, twin_channel=twin_channel)
                            except Exception as ex:
                                pass
                        # Сохраняем дату публикации
                        dt = datetime.now()
                        cr_dt = dt.replace(microsecond=0).timestamp()
                        post.last_published_dt = int(cr_dt)
                        post.save()
                        if (publicator.mode == PublicatorModes.New.value) or (publicator.mode == PublicatorModes.Premoderate.value):
                            publicator.last_post_id = post.post_id
                            publicator.save()
                            if debug: publicators_loger.info(
                                f'Публикатор {publicator.name}. Режим публикатора "Новые" или "Премодерация". Сохраняем последний id поста. Текущий час: {cur_time}. Период задержки {period} сек ({period / 60 / 60} часа).')
                            if publicator.delete_public_post == 1:
                                delete_post(post.get_id())
                            else:
                                post.moderate = ModerateStates.Published.value
                                post.save()
                        else:
                            # Если не новые то прекращаем размещения до следующего периода
                            if debug: publicators_loger.info(
                                f'Публикатор {publicator.name}. Режим одиночный - другие посты не размещаем. Текущий час: {cur_time}. Период задержки {period} сек ({period / 60 / 60} часа).')
                            if publicator.delete_public_post == 1:
                                delete_post(post.get_id())
                            break
                        # пауза между публикациями
                        if debug: publicators_loger.info(
                            f'Публикатор {publicator.name}. Пауза между публикациями. Текущий час: {cur_time}. Период задержки {period} сек ({period / 60 / 60} часа).')
                        await asyncio.sleep(publicator.public_delay)
                    except Exception as ex:
                        publicators_loger.error(f'Ошибка публикатора "{publicator.name}" при публикации поста {post.get_id()}: {ex}')
                publicator.save()
            # Спим
            if period > 0:
                if debug: publicators_loger.info(
                    f'Публикатор {publicator.name}. Спим указанный период. Текущий час: {cur_time}. Период задержки {period} сек ({period / 60 / 60} часа).')
                await asyncio.sleep(period)
            else:
                publicator.state = PublicatorStates.Done.value
                publicator.save()
                if debug: publicators_loger.info(
                    f'Публиктор {publicator.name}. Работа публикатора завершена'
                    f'. Текущий час: {cur_time}. Период задержки {period} сек ({period / 60 / 60} часа).')
                return
        except Exception as ex:
            publicators_loger.error(f'Ошибка процесса публикатора "{publicator.name}": {ex}')

async def init_current_publicators():
    '''Инициализация публикаторов
    Загрузка данных из базы и запуск потоков публикаторов'''
    # Загружаем данные из базы
    num = 0
    print(f'Запуск публикаторов...')
    app_loger.info(f'Запуск публикаторов...')
    try:
        publicators_mld = Publicator.select().where(Publicator.autostart==1)
        for publicator_mld in publicators_mld:
            # Создаем задачу
            publicator_task = asyncio.create_task(publicating(publicator_mld), name=publicator_mld.name)
            print(f'Запущен публикатор <{publicator_mld.name}>.')
            app_loger.info(f'Запущен публикатор <{publicator_mld.name}>.')
            num+=1
            current_publicators_process.append(publicator_task)
        print(f'Запущено {num} публикаторов.')
        app_loger.info(f'Запущено {num} публикаторов.')
    except Exception as ex:
        print(f'Инициализация публикаторов не удалась. Ошибка {ex}.')
        app_loger.error(f'Инициализация публикаторов не удалась. Ошибка {ex}.')



