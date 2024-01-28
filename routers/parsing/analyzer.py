'''Модуль отвечает за анализ спарсеных данных в формате APost
'''

import enum
import re
from dataclasses import dataclass
import hashlib
#

from models.data.post import Post
from models.data.criterion import VideoPlatform, UrlAction
#
from routers.parsing.text_analyze_tools import check_text_on_keywords, lematize_words
from routers.parsing.parsing_config import VOID_TEXT_CHAR
from routers.parsing.interface_parser import APost

class KeyWordsAnalyzeMode(enum.Enum):
    And = 0
    Or = 1

@dataclass
class AnalyzerParams:
    task_id: int
    target_id: int =  0
    hashtags: list[str] = None #
    clear_words: list[str] = None #
    forbidden_words: list[str] = None #
    #replace_words: dict = None
    replace_words: str = None
    key_words: list[str] = None #
    key_words_mode: KeyWordsAnalyzeMode = KeyWordsAnalyzeMode.Or  #
    post_start_date: int = 0 #
    post_end_date: int = 0 #
    max_text_len: int = 1000000 #
    min_text_len: int = 700 #
    last_post_id: int = 0 #
    lematize: bool = True
    video_platform: int = 0 # С каких платформ собирать видео 0 - со всех
    del_hashtags: bool = False # Удалять или нет хэштэги
    url_action: int = 0  # что делать с постами в тексте которых есть ссылки

def check_video_platform(videos: list, video_platform: int)-> list:
    '''Проверяет пост на соответсвие видеоплатвормы'''
    new_video=[]
    if video_platform == VideoPlatform.OnlyYouTube.value:
        cond = 'youtube.com/'
    elif video_platform == VideoPlatform.OnlyVK.value:
        cond = 'vk.com/'
    elif video_platform == VideoPlatform.Ignore.value:
        return new_video
    elif video_platform == VideoPlatform.All.value:
        return videos
    else:
        return new_video
    for video in videos:
        if video['url'].find(cond) != -1:
            new_video.append(video)
    return new_video

def check_text(text: str, forbidden_words: list[str]) -> bool:
    '''Проверяет текст на наличие запрещенных слов'''
    res = True
    if type(forbidden_words) is str:
        forbidden_words = forbidden_words.replace(', ', ',')
        forbidden_words = forbidden_words.split(',')
    forbidden_words = [x.strip() for x in forbidden_words]
    forbidden_words_low = [x.upper() for x in forbidden_words]
    forbidden_words_up = [x.lower() for x in forbidden_words]
    forbidden_words.extend(forbidden_words_low)
    forbidden_words.extend(forbidden_words_up)
    for forbidden_word in forbidden_words:
        if text.find(forbidden_word) != -1:
            res = False
            return res
    return res

def check_text_on_keywords_ex(text: str, key_words: list[str], mode: KeyWordsAnalyzeMode) -> bool:
    '''Проверяет текст на наличие ключевых слов, если хотябы одно есть возвращает True'''
    if mode == KeyWordsAnalyzeMode.Or:
        res = False
        for key_word in key_words:
            if text.find(key_word) != -1:
                res = True
                return res
        return res
    elif mode == KeyWordsAnalyzeMode.And:
        res = True
        for key_word in key_words:
            if text.find(key_word) == -1:
                res = False
                return res
        return res

def check_hashtags(hashtags_str, hashtags: list[str]) -> bool:
    '''Проверяет соответсвтие хэштегов'''
    res = False
    hashtags_str = hashtags_str.replace(', ', ',')
    hashtags_str = hashtags_str.split(',')
    hashtags_str = [x.lower() for x in hashtags_str]
    hashtags_str = [x.strip() for x in hashtags_str]
    for ht in hashtags_str:
        if ht in hashtags:
            res = True
            return res
    return res

def delete_hashtags(text: str) -> str:
    '''Удаление из текста хэштегов'''
    entity_prefixes = ['@', '#']
    words = []
    for word in text.split():
        word = word.strip()
        if word:
            if word[0] not in entity_prefixes:
                words.append(word)
    return ' '.join(words)

def check_url(text: str) -> bool:
    res = True
    if text.find('https:') != -1 or text.find('http:') != -1 or text.find('www.') != -1 or \
    text.find('.com') != -1 or text.find('.ru') != -1 or text.find('club') != -1 or text.find('vk.cc') != -1:
        res = False
    return res

def clear_url(text: str) -> str:
    '''Удаляет из текста ссылки'''
    res = True
    url_tags = ['https:', 'http:', 'www.', '.com', '.ru', 'club', 'vk.cc']
    for tag in url_tags:
        pos_s = 1
        while pos_s != -1:
            pos_s = text.find(tag)
            if pos_s != -1:
                pos_e = text.find(' ', pos_s)
                if pos_e != -1:
                    text1 = text[:pos_s]
                    text2 = text[pos_e-1:]
                    text = f'{text1}{text2}'
                else:
                    text = text[:pos_s]
                    pos_s = -1
    return text

def replace_words_in_text(text: str, words: dict) -> str:
    for key in words.keys():
        old_word = key
        new_word = words[key]
        text = text.replace(old_word, new_word)
    return text


async def analyze_posts(posts: list[APost], params: AnalyzerParams) -> list[APost]:
    '''
    Выбираем из спарсеного массива постов те, которые соответсвют заданным критериям задачи
    '''
    res = []
    for i, post in enumerate(posts):
        # Анализируем длинну текст
        if len(posts[i].text) < params.min_text_len:
            continue
        if len(posts[i].text) > params.max_text_len:
            continue
        # Проверяем дату публикации поста
        if params.post_end_date != None and params.post_end_date != 0:
            if params.post_end_date > 0 and post.dt > params.post_end_date:
                continue
        if params.post_start_date != None and params.post_start_date != 0:
            if params.post_start_date > 0 and post.dt < params.post_start_date:
                continue
        # Проверяем чтобы уже добавленые посты не добавлялись
        # if (params.last_post_id != 0) and (post.post_id <= params.last_post_id):
        #     continue
        tmp_post = Post.get_post(post_id=post.post_id, task_id=params.task_id, source_id=params.target_id)
        if tmp_post != None:
            continue
        # Проверяем хэштэги
        if params.hashtags != None and params.hashtags != '':
            if not check_hashtags(params.hashtags, post.hashtags):
                continue
        # Проверяем соответсвие видеоплатфоме
        if params.video_platform != None and params.video_platform != 0 and len(post.videos)>0:
            new_video = check_video_platform(post.videos, params.video_platform)
            if len(new_video)==0:
                continue
            else:
                post.videos = new_video
        # Проверяем ссылки в тексте
        if params.url_action == UrlAction.Delete.value:
            posts[i].text = clear_url(posts[i].text)
        if params.url_action == UrlAction.Ignore.value:
            if not check_url(posts[i].text):
                continue
        # Если в тексте есть запрещенные слова то пропускаем
        if params.forbidden_words != None:
            if not check_text(posts[i].text, params.forbidden_words):
                continue
        # Если необходимо удаляем из текста хэштеги
        if params.del_hashtags:
            posts[i].text = delete_hashtags(posts[i].text)
        # Проверяем текст на ключевые слова
        if not params.lematize:
            if params.key_words != None and params.key_words != '':
                if not check_text_on_keywords_ex(posts[i].text, params.key_words, params.key_words_mode):
                    continue
        else:
            if params.key_words != None and params.key_words != '':
                lem_words = lematize_words(params.key_words)
                migths = check_text_on_keywords(posts[i].text, lem_words, normalize=True)
                if type(migths) is not dict:
                    raise ValueError(migths)
                if params.key_words_mode == KeyWordsAnalyzeMode.Or:
                    cond = False
                    for migth in migths.values():
                        if migth > 0:
                            cond = True
                            break
                else:
                    cond = True
                    for migth in migths.keys():
                        if migth == 0:
                            cond = False
                            break
                if cond == False:
                    continue
        # Заменяем слова
        if params.replace_words != None:
            try:
                rep_words = eval(params.replace_words)
                posts[i].text = replace_words_in_text(posts[i].text, rep_words)
            except:
                pass
        # Очищаем от заданных слов
        if params.clear_words != None:
            clear_words = params.clear_words
            if type(clear_words) is str:
                clear_words = clear_words.replace(', ', ',')
                clear_words = clear_words.split(',')
            clear_words = [x.strip() for x in clear_words]
            clear_words_low = [x.upper() for x in clear_words]
            clear_words_up = [x.lower() for x in clear_words]
            clear_words.extend(clear_words_low)
            clear_words.extend(clear_words_up)
            for cl_word in clear_words:
                posts[i].text = posts[i].text.replace(cl_word, '')
        # Удаляем внутренние ссылки ВК
        posts[i].text = re.sub(r'\[.+?\]\s', '', posts[i].text)
        # Проверяем текст на уникальность по хэшу
        hash = hashlib.md5(posts[i].text.encode('utf-8'))
        hash_str = hash.hexdigest()
        if posts[i].text != VOID_TEXT_CHAR:
            post_ex = Post.get_post(task_id=params.task_id, source_id=params.target_id, text_hash=hash_str)
            if post_ex != None:
                continue
        posts[i].text_hash = hash_str
        res.append(posts[i])
    return res

