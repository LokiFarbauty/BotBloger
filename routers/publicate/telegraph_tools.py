from typing import Union
from telegraph import Telegraph
#
from models.data.post import Post
from models.data.post_hashtag import Post_Hashtag
from models.data.video import Video
from models.data.link import Link
from models.data.audio import Audio
from models.data.docs import Doc
from models.data.poll import Poll
from models.data.photo import Photo
from models.data.post_text_FTS import PostText
import models.data_model as data_model
#
from routers.logers import publicators_loger


def get_url_name(text: str, prefix: str = ''):
    if prefix != '':
        pos_start = text.find(prefix)
        pos_end = text.find('</a>', pos_start)
        if pos_start != -1 and pos_end != -1:
            res = text[pos_start + len(prefix):pos_end]
        else:
            res = ''
    else:
        pos_start = text.find('<a href="')
        pos_end = text.find('">', pos_start)
        if pos_start != -1 and pos_end != -1:
            res = text[pos_start + len('<a href="'):pos_end]
        else:
            res = ''
    return res

def text_to_telegraph_format(text: str) -> str:
    '''Функция заменяет абзацы \n на html параграфы'''
    res_text = ''
    pos = text.find('\n')
    if pos != -1:
        par_start = text[:pos].strip()
        res_text = f'{res_text}<p>{par_start}</p>\n'
    else:
        return f'<p>{text}</p>'
    while pos != -1:
        # ищем следующий перенос
        pos_end = text.find('\n', pos + 1)
        if pos_end == -1:
            # Больше переносов нет
            par = text[pos + 1:]
        else:
            par = text[pos + 1:pos_end]
        # закидываем параграф в текст
        par = par.strip()
        if par != '':
            res_text = f'{res_text}<p>{par}</p>\n'
        pos = pos_end
    return res_text

async def put_post_to_telegraph(post: Post, telegraph_token, author_name='', author_url='', author_caption=''):
    # Создаем страничку в Телеграфе
    tg_url = ''
    try:
        telegraph = Telegraph(access_token=telegraph_token)
        post_key = post.get_id()
        # Получаем текст
        post_index = PostText.get_by_id(post_key)
        post_text = post_index.text
        # Определяем заголовок
        tlink = get_url_name(post_text, prefix='Продолжение -> ')
        if tlink == '':
            title = ''
        else:
            title = tlink
        if title == '':
            pos = post_text.find('\n')
            if pos == -1 or pos > 50:
                pos = post_text.find('.')
            if pos == -1 or pos > 50:
                pos = post_text.find(' ')
            if pos != -1 and pos <= 50:
                title = post_text[:pos]
            else:
                # Берем название из хэштэгов
                hashtags = Post_Hashtag.get_post_hashtags_str(post)
                hashtags = hashtags.strip()
                if hashtags != '':
                    title = hashtags
                else:
                    title = ''
        if title == '':
            title = 'Без названия'
        # Добавляем в текст линки
        links = Link.select().where(Link.owner == post)
        for link in links:
            post_text = f'{post_text}\n<a href="{link.url}">{link.title}</a>'
        # Получаем картинки
        photos = Photo.select().where(Photo.owner == post)
        photo_urls = ''
        for photo in photos:
            photo_urls = f'{photo_urls}<img src="{photo.url}" alt="{photo.caption}">'
        post_text = f'{photo_urls}\n{post_text}'
        # Порлучаем видео
        videos = Video.select().where(Video.owner == post)
        video_urls = ''
        for video in videos:
            #video_urls = f'{video_urls}\n<a href="{video.url}">{video.title}</a>'
            if video.url.find('youtube') != -1:
                video_urls = f'{video_urls}\n<figure><iframe src="/embed/youtube?url={video.url}"></iframe></figure>'
            else:
                video_urls = f'{video_urls}\n<a href="{video.urll}">{video.title}</a>'
        post_text = f'{video_urls}\n{post_text}'
        # Форматируем текст
        post_text = f'{post_text}\n{author_caption}'
        post_text = text_to_telegraph_format(post_text)
        res = telegraph.create_page(title, html_content=post_text,
                                         author_name=author_name,
                                         author_url=author_url)
        tg_url = res['url']
    except Exception as ex:
        publicators_loger.error(f'Не удалось создать страничку на telegrap.ph. Причина: {ex}')
    return tg_url
