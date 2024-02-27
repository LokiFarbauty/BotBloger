'''Этот модуль отвечает за сохранение спарсеной информации в базу'''


import enum
import logging
#
from models.data.post_text_FTS import PostText
from models.data.post import Post
from models.data.parse_task import ParseTask
from models.data.parse_program import ParseProgram
from models.data.hashtag import Hashtag
from models.data.post_hashtag import Post_Hashtag
from models.data.photo import Photo
from models.data.link import Link
from models.data.poll import Poll
from models.data.video import Video
from models.data.audio import Audio
from models.data.docs import Doc
#
from routers.parsing.interface_parser import APost
# logers
from routers.logers import parsers_loger

class SaverErrors(enum.Enum):
    NoError = 'данные успешно сохранены'
    PyError = 'ошибка сохранения данных'

async def save_posts(posts: list[APost], target_id: int, task: ParseTask, program: ParseProgram = None):
    '''
    Сохраняем посты в базу
    :param posts:
    target_id - id источника информации
    task - задача парсинга
    :return:
    '''
    try:
        for post in posts:
            tg_url = ''
            # Сохраняем текст и пост
            post_index = PostText.create(text=post.text)
            post_index.save()
            post_index_id = post_index.get_id()
            post_obj = Post.create(post_id=post.post_id, source_id=target_id, text=post_index_id, views=0,
                                   old_views=post.views, likes=post.likes, dt=post.dt,
                                   telegraph_url=tg_url, text_hash=post.text_hash, parse_task=task, parse_program=task.program,
                                   moderate=task.moderated, last_published_dt=0, text_len=len(post.text), rate=post.rate)
            post_obj.save()
            # Сохраняем хэштеги
            for hashtag in post.hashtags:
                # Проверяем существует ли такой хэштег
                hashtag_obj = Hashtag.get_hashtag(hashtag)
                if hashtag_obj == None:
                    hashtag_obj = Hashtag.create(value=hashtag)
                    hashtag_obj.save()
                post_hashtag = Post_Hashtag.create(post=post_obj, hashtag=hashtag_obj)
                post_hashtag.save()
            # Сохраняем картинки
            for photo in post.photos:
                photo_obj = Photo.create(owner_id=post_obj, caption=photo['caption'], url=photo['url'])
                photo_obj.save()
            # Сохраняем ссылки
            for link in post.links:
                link_obj = Link.create(owner_id=post_obj, description=link['description'], url=link['url'], title=link['title'])
                link_obj.save()
            # Сохраняем опросы
            for poll in post.polls:
                poll_obj = Poll.create(owner_id=post_obj, question=poll['question'], answers=poll['answers'],
                                       anonymous=poll['anonymous'], multiple=poll['multiple'])
                poll_obj.save()
            # Сохраняем видео
            for video in post.videos:
                video_obj = Video.create(owner_id=post_obj, title=video['title'], url=video['url'], description=video['description'], duration=video['duration'])
                video_obj.save()
            # Сохраняем аудио
            for audio in post.audios:
                audio_obj = Audio.create(owner_id=post_obj, artist=audio['artist'], url=audio['url'], title=audio['title'])
                audio_obj.save()
            # Сохраняем документы
            for doc in post.docs:
                doc_obj = Doc.create(owner_id=post_obj, url=doc['url'])
                doc_obj.save()
        return SaverErrors.NoError
    except Exception as ex:
        # if logger != None:
        #     logger.error(f'Ошибка в save_posts: {ex}')
        parsers_loger.error(f'save_posts(target_id={target_id}, task={task.get_id()}, program={program.get_id()}): {ex}')
        return SaverErrors.PyError