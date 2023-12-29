'''Модуль отвечает за анализ спарсеных данных в формате APost
'''

import enum
import re
from dataclasses import dataclass
import hashlib
#
from routers.parsing.interface_parser import APost
from models.data.post import Post
from routers.parsing.text_analyze_tools import check_text_on_keywords, lematize_words

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
    key_words: list[str] = None #
    key_words_mode: KeyWordsAnalyzeMode = KeyWordsAnalyzeMode.Or  #
    post_start_date: int = 0 #
    post_end_date: int = 0 #
    max_text_len: int = 1000000 #
    min_text_len: int = 700 #
    last_post_id: int = 0 #
    lematize: bool = True


def check_text(text: str, forbidden_words: list[str]) -> bool:
    '''Проверяет текст на наличие запрещенных слов'''
    res = True
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
    res = True
    if type(hashtags_str) is str:
        hashtags_str = hashtags_str.replace('#', '')
        for hashtag in hashtags:
            hashtag0 = hashtag.replace('#', '')
            if hashtags_str.find(hashtag0) == -1:
                res = False
                return res
    elif type(hashtags_str) is list:
        for hashtag in hashtags:
            hashtag0 = hashtag.replace('#', '')
            if hashtag0 not in hashtags_str:
                res = False
                return res
    return res


async def analyze_posts(posts: list[APost], params: AnalyzerParams) -> list[APost]:
    '''
    Выбираем из спарсеного массива постов те, которые соответсвют заданным критериям задачи
    '''
    res = []
    for i, post in enumerate(posts):
        # Анализируем длинну текста
        if len(post.text) < params.min_text_len:
            continue
        if len(post.text) > params.max_text_len:
            continue
        # Проверяем дату публикации поста
        if params.post_end_date > 0 and post.dt > params.post_end_date:
            continue
        if params.post_start_date > 0 and post.dt < params.post_start_date:
            continue
        # Проверяем чтобы уже добавленые посты не добавлялись
        if (params.last_post_id != 0) and (post.post_id <= params.last_post_id):
            continue
        # Проверяем хэштэги
        if params.hashtags != None:
            if not check_hashtags(post.hashtags, params.hashtags):
                continue
        # Если в тексте есть запрещенные слова то пропускаем
        if params.forbidden_words != None:
            if not check_text(post.text, params.forbidden_words):
                continue
        # Проверяем текст на ключевые слова
        if not params.lematize:
            if params.key_words != None:
                if not check_text_on_keywords_ex(post.text, params.key_words, params.key_words_mode):
                    continue
        else:
            if params.key_words != None:
                lem_words = lematize_words(params.key_words)
                migths = check_text_on_keywords(post.text, lem_words, normalize=True)
                if params.key_words_mode == KeyWordsAnalyzeMode.Or:
                    cond = False
                    for migth in migths.keys():
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
        # Очищаем от заданных слов
        if params.clear_words != None:
            for cl_word in params.clear_words:
                posts[i].text = post.text.replace(cl_word, '')
        # Удаляем внутренние ссылки ВК
        posts[i].text = re.sub(r'\[.+?\]\s', '', post.text)
        # Проверяем текст на уникальность по хэшу
        hash = hashlib.md5(posts[i].text.encode('utf-8'))
        hash_str = hash.hexdigest()
        post_ex = Post.get_post(task_id=params.task_id, source_id=params.target_id, text_hash=hash_str)
        if post_ex != None:
            continue
        posts[i].text_hash = hash_str
        res.append(post)
    return res

