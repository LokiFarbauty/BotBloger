import aiohttp
# routers
from routers.console.terminal_interface import Command
from routers.parsing.parsers_dispatсher import parsers_dispatcher
from routers.parsing.interface_parser import ParseParams
from routers.parsing.analyzer import analyze_posts, AnalyzerParams
#
from models.saver import save_posts
from models.data.parse_task import ParseTask
from models.data.post import Post
from models.data.publicator import Publicator
#
from routers.logers import app_loger
from routers.parsing.parsing import parsing
from routers.publicate.telegraph_tools import put_post_to_telegraph
from routers.publicate.publicators import (public_post_to_channel, get_publicator_process_state,
                                           stop_publicator_process, start_publicator_process)
from routers.parsing.rating import refresh_posts_rating
import yt_dlp
from main_config import MAIN_PATH
import translators as ts

commands = []

# commands.append(
#      Command(name='get_users', func=User.get_users_obj, args_num=1, help='Получить пользователей из базы данных. Параметры: 1 - user_id либо username.')
# )

async def vk_parse(target_id=0, token='test'):
    # Быстрое получение токена https://vkhost.github.io/
    token_old = 'vk1.a.fZyiWIVGGg_7sM0euOzteiauES3ZM2DP73QXvWnMaAR2lc7-ww2bms3zWifrqKDTTeUAkW06-sEAiHJLxZwKcTlZaQD-q_EQZatNZOK_XTXp7Y3FVMqi6THV29qM96AIDfNmEMR3Fkg1rNTnObyCqbn9wQmsbWsCBSmYHflU9cOyy-Dc4i1g1QdiWQxmKiPrTu7hicXNU-3TrVvzrLIXSA'
    token_new = 'vk1.a.irNTOTLoYE_IiEpdQbE72U2VZe02ZfC8VLN91jmoD6x1I2crOoLOB4yb-DAL_2HmupsK5tqLHvQxmm_73TjumR7CgJvsVCrtcvFeud-e2NA4tYxGynqAdwVQJd3KVt5tNLkr_CVKGACQR0JnW8OKR87Ij3C8FS4MtQn9pnD5eFri6BebEkW77OFlRW1zo8rb7zIpZjyRZo1mSup_1sBOUg'
    res_token = 'vk1.a.91iecxcqhaZpqlRZ5aSZPvTJa9LmJbYPNCUkefQgipRIBZBmNoFVFOCNndqcrfchsa1a0Cj0mo0pQVMyW5Gt-nEoxnvvgBaVnbh3Z7du_enxoTlC0zPKmvpw0D1tOHzA9oTwwp3KG0jElf5VV6DL78NEmCafwO-ZzwuXEg3C4TAd8PM3A1dPZ2uNFfnHkOk-synIYGhT52OhG-exMjjXxQ'
    if token == 'test':
        token = token_new
    params = ParseParams(target_id=target_id, token=token, post_count=10, use_free_proxy=False)
    parser = parsers_dispatcher.get_parser('ВКонтакте')
    if parser != None:
        conn = aiohttp.TCPConnector(limit=None, ttl_dns_cache=300)
        async with aiohttp.ClientSession(connector=conn) as new_session:
            parse_res= await parser.parse(params, session=new_session)
    else:
        return 'Парсер не найден'
    # Анализ
    #
    task = ParseTask.get_task(name='test')
    if task == None:
        task = ParseTask.create(name='test', last_post_id=0, filter='all', cr_dt=0, active=0)
    params = AnalyzerParams(task_id=task.get_id(), target_id=target_id, min_text_len=10)
    proc_posts = await analyze_posts(parse_res, params)
    await save_posts(proc_posts, target_id, task=task)
    #
    res = []
    if proc_posts !=[]:
        for rec in proc_posts:
           res.append(rec.text)
    else:
        res = 'Подходящих постов не обнаружено'
    return res

commands.append(
     Command(name='vk_parse', func=vk_parse, args_num=1, help='Получить данные со стены страницы ВКонтакте. Параметры: 1 - target_id (id объекта ВК)')
)

async def get_vk_post_count(target_id=0, token='test'):
    if token == 'test':
        token = 'vk1.a.fZyiWIVGGg_7sM0euOzteiauES3ZM2DP73QXvWnMaAR2lc7-ww2bms3zWifrqKDTTeUAkW06-sEAiHJLxZwKcTlZaQD-q_EQZatNZOK_XTXp7Y3FVMqi6THV29qM96AIDfNmEMR3Fkg1rNTnObyCqbn9wQmsbWsCBSmYHflU9cOyy-Dc4i1g1QdiWQxmKiPrTu7hicXNU-3TrVvzrLIXSA'
    params = ParseParams(target_id=target_id, token=token, post_count=1, use_free_proxy=False)
    parser = parsers_dispatcher.get_parser('ВКонтакте')
    if parser != None:
        res=await parser.get_entries_count(params)
    else:
        return 'Парсер не найден'
    return res

commands.append(
     Command(name='get_vk_post_count', func=get_vk_post_count, args_num=1, help='Получить количество записей на стене страницы ВКонтакте. Параметры: 1 - target_id (id объекта ВК)')
)

async def get_vk_id(target_name, token='test'):
    if token == 'test':
        token = 'vk1.a.fZyiWIVGGg_7sM0euOzteiauES3ZM2DP73QXvWnMaAR2lc7-ww2bms3zWifrqKDTTeUAkW06-sEAiHJLxZwKcTlZaQD-q_EQZatNZOK_XTXp7Y3FVMqi6THV29qM96AIDfNmEMR3Fkg1rNTnObyCqbn9wQmsbWsCBSmYHflU9cOyy-Dc4i1g1QdiWQxmKiPrTu7hicXNU-3TrVvzrLIXSA'
    parser = parsers_dispatcher.get_parser('ВКонтакте')
    if parser != None:
        id, type = await parser.get_vk_object_id(target_name, token, with_type=True)
    else:
        return 'Парсер не найден'
    return f'id: {id}, type: {type}'

commands.append(
     Command(name='get_vk_id', func=get_vk_id, args_num=1, help='Получить id страницы ВКонтакте. Параметры: 1 - название страницы (в id объекта ВК для сообщества нужно ставить знак "-")')
)

async def get_vk_group_info(target_id, token='test'):
    if token == 'test':
        token = 'vk1.a.fZyiWIVGGg_7sM0euOzteiauES3ZM2DP73QXvWnMaAR2lc7-ww2bms3zWifrqKDTTeUAkW06-sEAiHJLxZwKcTlZaQD-q_EQZatNZOK_XTXp7Y3FVMqi6THV29qM96AIDfNmEMR3Fkg1rNTnObyCqbn9wQmsbWsCBSmYHflU9cOyy-Dc4i1g1QdiWQxmKiPrTu7hicXNU-3TrVvzrLIXSA'
    parser = parsers_dispatcher.get_parser('ВКонтакте')
    if parser != None:
        res = await parser.get_vk_group_info(target_id, token)
    else:
        return 'Парсер не найден'
    return res

commands.append(
     Command(name='get_vk_group_info', func=get_vk_group_info, args_num=1, help='Возвращает информацию о группе ВКонтакте. Параметры: 1 - id группы (в id объекта ВК для сообщества нужно ставить знак "-")')
)

async def get_vk_user_group(target_id, filter='', token='test'):
    if token == 'test':
        token = 'vk1.a.91iecxcqhaZpqlRZ5aSZPvTJa9LmJbYPNCUkefQgipRIBZBmNoFVFOCNndqcrfchsa1a0Cj0mo0pQVMyW5Gt-nEoxnvvgBaVnbh3Z7du_enxoTlC0zPKmvpw0D1tOHzA9oTwwp3KG0jElf5VV6DL78NEmCafwO-ZzwuXEg3C4TAd8PM3A1dPZ2uNFfnHkOk-synIYGhT52OhG-exMjjXxQ'
    parser = parsers_dispatcher.get_parser('ВКонтакте')
    if parser != None:
        res = await parser.get_vk_user_group(target_id, token, filter)
    else:
        return 'Парсер не найден'
    return res

commands.append(
     Command(name='get_vk_user_group', func=get_vk_user_group, args_num=1, help='Возвращает список групп и пабликов ВКонтакте в которых состоит пользователь, при фильтре админ, вернет группы, где он администратор. Параметры: 1 - id пользователя; 2 - фильтр (admin, moder, editor)')
)

async def get_task_process_status(taskname: str):
    res = parsers_dispatcher.get_task_status(taskname)
    return res.value

commands.append(
     Command(name='get_task_process_status', func=get_task_process_status, args_num=1, help='Возвращает статус процесса задачи. Параметры: 1 - имя задачи')
)

async def stop_task_process(taskname: str):
    res = parsers_dispatcher.stop_task(taskname)
    return res

commands.append(
     Command(name='stop_task_process', func=stop_task_process, args_num=1, help='Останвливает процесс задачи. Параметры: 1 - имя задачи')
)

async def start_task_process(taskname: str):
    res = await parsers_dispatcher.start_task(taskname=taskname, func=parsing)
    return res

commands.append(
     Command(name='start_task_process', func=start_task_process, args_num=1, help='Запускает процесс задачи. Параметры: 1 - имя задачи')
)

async def get_publicator_process_status(name: str):
    task_state = get_publicator_process_state(name)
    return task_state

commands.append(
     Command(name='get_publicator_process_status', func=get_publicator_process_status, args_num=1, help='Возвращает статус процесса публикатора. Параметры: 1 - имя публикатора')
)

async def stop_publicator(name: str):
    res = stop_publicator_process(name)
    return res

commands.append(
     Command(name='stop_publicator', func=stop_publicator, args_num=1, help='Останвливает процесс публикатора. Параметры: name: str')
)

async def start_publicator(name: str):
    res = f'Публикатор "{name}" не найден.'
    try:
        publicator = Publicator.get_publicator(name=name)
        if publicator != None:
            res = start_publicator_process(publicator)
            return res
    except Exception as ex:
        res = f'Ошибка {ex}'
    return res

commands.append(
     Command(name='start_publicator', func=start_publicator, args_num=1, help='Запускает процесс публикатора. Параметры: name: str')
)

async def put_post_in_telegraph(post_key: int):
    try:
        post = Post.get_by_id(post_key)
        res = await put_post_to_telegraph(post, telegraph_token='56cbd6664bcc26ea2e247b50805cb2c3c12efc70bbf3d3dd5148ee1a02ad',
                                          author_name='Loki', author_caption='Благодарим за внимание!', author_url='')
    except Exception as ex:
        res = ex
    return res

commands.append(
     Command(name='put_post_in_telegraph', func=put_post_in_telegraph, args_num=1, help='Размещает пост в телеграфе. Параметры: 1 - ключ поста')
)

async def public_post_test(publicator_key: int, post_key: int):
    try:
        post = Post.get_by_id(post_key)
        publicator = Publicator.get_by_id(publicator_key)
        res = await public_post_to_channel(publicator, post)
    except Exception as ex:
        res = ex
    return res

commands.append(
     Command(name='public_post_test', func=public_post_test, args_num=2, help='Размещает пост в канале. Параметры: 1 - ключ публикатора. 2 - ключ поста')
)

async def calc_rate(parse_task_id: int):
    parse_task = ParseTask.get_by_id(parse_task_id)
    await refresh_posts_rating(parse_task)
    return 'Расчет рейтинга выполнен'

commands.append(
     Command(name='calc_rate', func=calc_rate, args_num=1, help='Рассчитать рейтинг постов для задачи. Параметры: 1 - parse_task_id (id задачи)')
)

async def download_video(video_url: str):
    try:
        output_directory = f'{MAIN_PATH}/downloads'
        ydl_opts = {'outtmpl': f'{output_directory}/%(title)s.%(ext)s'}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
            info = ydl.extract_info(video_url, download=True)
        return f"Видео успешно скачано\n «{info['title']}»"
    except Exception as ex:
        return f'Error: {ex}'

commands.append(
     Command(name='download_video', func=download_video, args_num=1, help='Скачать видео по ссылке. Параметры: 1 - url (ссылка на видео)')
)

async def translate_text(text: str, lang: str = 'en'):
    try:
        tr_text = ts.translate_text(text)
        #tr_text = ts.get_languages()
        return tr_text
    except Exception as ex:
        return f'Error: {ex}'

commands.append(
     Command(name='translate_text', func=translate_text, args_num=1, help='Перевести текст. Параметры: 1 - текст, 2 - язык (необязательно)')
)