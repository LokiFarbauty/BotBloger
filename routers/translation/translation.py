import translators as ts

RUS = 'ru' #
ENG = 'en' #
CHN = 'zh_Hans'
ISP = 'es'
IND = 'hi'
PTG = 'pt'
GER = 'de'
FRA = 'fr'
UKR = 'uk'
KOR = 'ko'
POL = 'pl'
TUR = 'tr'

def translate_text(text, to_language = ENG):
    post_text = text
    translators_lst = ['bing', 'google', 'yandex', 'baidu', 'deepl']
    for translator in translators_lst:
        try:
            post_text = ts.translate_text(post_text, translator=translator, to_language=to_language)
            break
        except Exception as ex:
            pass
    return post_text