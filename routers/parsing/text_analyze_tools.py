'''Всякие полезные функции для анализа текстов'''

from gensim.parsing.preprocessing import remove_stopwords
from gensim.utils import simple_preprocess
import string
import pymorphy3


stop_words_list=['в', 'не', 'и', 'а', 'но', 'при', 'тогда', 'до', 'после', 'под', 'на', '-на', 'без', 'для', 'за', 'через', 'над', 'по', 'из', 'у', 'же', '-нибудь',
                 'около', 'о', 'про', 'к', 'перед', 'с', 'между', 'так' 'как', 'однако', 'зато', 'чтобы', 'либо', 'или', 'что', 'если', 'хотя', 'пока', 'от', 'во', 'из-под', 'из-за', 'то', '-то',
                 'В', 'Не', 'И', 'А', 'Но', 'При', 'Тогда', 'До', 'После', 'Под', 'На', 'Без', 'Для', 'За',
                 'Через', 'Над', 'По', 'Из', 'У', 'Же', 'Нибудь',
                 'Около', 'О', 'Про', 'К', 'Перед', 'С', 'Между', 'Так' 'Как', 'Однако', 'Зато', 'Чтобы', 'Либо', 'Или',
                 'Что', 'Если', 'Хотя', 'Пока', 'От', 'Во', 'Из-под', 'Из-за', 'То', 'также', 'Также']


def remove_specchars_from_text(text, chars):
    return "".join([ch for ch in text if ch not in chars])

def tokenize_text(text: str, normalize: bool = True, join_char=''):
    if text == '':
        return []
    try:
        # Определяем анализатор
        morph = pymorphy3.MorphAnalyzer()
        # Удаляем из текста спецсимволы и стопслова
        spec_chars = string.punctuation + '\n\xa0«»\t—…'
        text = remove_specchars_from_text(text, spec_chars)
        text = remove_specchars_from_text(text, string.digits)
        filtered_text = remove_stopwords(text, stop_words_list)
        tokenized = simple_preprocess(filtered_text, deacc=False, min_len=2, max_len=20)
        norm_tokenized = []
        if normalize:
            for i in range(len(tokenized)):
                word = tokenized[i]
                norm_words = morph.parse(word)
                if type(norm_words) is not str:
                    for norm_word in norm_words:
                        if f'{join_char}{norm_word.normal_form}' not in norm_tokenized:
                            norm_tokenized.append(f'{join_char}{norm_word.normal_form}')
                else:
                    norm_tokenized.append(norm_words.normal_form)
        else:
            norm_tokenized = tokenized
        return norm_tokenized
    except Exception as ex:
        return ex

def check_text_on_hashtags(text: str, hashtags: list):
    res = True
    hashtag_ex=[]
    for hashtag in hashtags:
        res0 = False
        ext=text.find(hashtag)
        if ext != -1:
            res0 = True
        hashtag_ex.append(res0)
    if False in hashtag_ex:
        res = False
    return res

def lematize_words(words: list[str]) -> list[str]:
    morph = pymorphy3.MorphAnalyzer()
    res=[]
    if type(words) is str:
        words = words.replace(', ', ',')
        words = words.split(',')
    words = [x.lower() for x in words]
    words = [x.strip() for x in words]
    for word in words:
        norm_word = morph.parse(word)
        res.append(norm_word[0].normal_form)
    return res


def check_text_on_keywords(text: str, keywords: list, normalize=True):
    '''
    Функция проверяет текст на ключевые слова с учетом лематизации
    :param text: нелематизмрованный текст
    :param keywords: список лематизированых ключевых слов
    :param normalize:
    :return: возвращает словарь с количеством вхождений в текст каждого слова
    '''
    try:
        # Токенизируем текст
        # Определяем анализатор
        morph = pymorphy3.MorphAnalyzer()
        # Удаляем из текста спецсимволы и стопслова
        spec_chars = string.punctuation + '\n\xa0«»\t—…'
        text = remove_specchars_from_text(text, spec_chars)
        text = remove_specchars_from_text(text, string.digits)
        filtered_text = remove_stopwords(text, stop_words_list)
        tokenized = simple_preprocess(filtered_text, deacc=False, min_len=2, max_len=20)
        if normalize:
            norm_tokenized = []
            for i in range(len(tokenized)):
                word = tokenized[i]
                norm_words = morph.parse(word)
                if type(norm_words) is not str:
                    for norm_word in norm_words:
                        if norm_word.normal_form not in norm_tokenized:
                            norm_tokenized.append(norm_word.normal_form)
                else:
                    norm_tokenized.append(norm_words.normal_form)
        else:
            norm_tokenized = tokenized
        # Проверяем текст на ключевые слова и считаем количество вхождений
        mights = {}
        for keyword in keywords:
            mights[keyword] = 0
            if keyword in norm_tokenized:
                mights[keyword]+=1
        return mights
    except Exception as ex:
        return ex