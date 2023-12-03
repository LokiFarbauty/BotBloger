from aiogram.types import User
from math import ceil

def get_tg_user_names(tg_user: User, default= ''):
    '''Возвращает имена пользователя в телеграмм боте'''
    try:
        username = str(tg_user.username)
        if username == 'None':
            username = ''
    except:
        username = default
    try:
        first_name = str(tg_user.first_name)
        if first_name == 'None':
            first_name = ''
    except:
        first_name = default
    try:
        last_name = str(tg_user.last_name)
        if last_name == 'None':
            last_name = ''
    except:
        last_name = default
    return username, first_name, last_name

def del_forbiden_tg_char(oldstr: str):
    newstr = oldstr.replace("'", "")
    newstr = newstr.replace("|", "")
    newstr = newstr.replace(">", "")
    newstr = newstr.replace("<", "")
    return newstr

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

def check_mat_in_text(text: str):
    res = False
    mat_words = ['хуй', 'хуёв', 'хуев', 'пизд', ' бля ', 'блять', ' бляд', 'ебать', 'ебаный', 'ебанут', 'ёбаный', 'русня', 'ебал', 'путлер',
                 'пидор', ' гей ', ' геи ', 'лесби', 'русак', ' хач', ' чурка ', ' жид ', ' жиды ', ' жидов', ' пыня ', ' навальный ', 'свинорус']
    for word in mat_words:
        if text.find(word)!=-1:
            res = True
            return res
        if text.find(word.upper())!=-1:
            res = True
            return res
    return res

