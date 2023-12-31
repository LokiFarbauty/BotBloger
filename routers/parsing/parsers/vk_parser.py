'''Модуль содержит парсер для ВКонтакте, созданный согласно соглашению взаимодействия ParserInterface'''

from routers.parsing.interface_parser import ParserInterface, ParseParams, ParserInterfaceReturns, APost
import logging
from typing import Union
from fake_useragent import UserAgent
import requests
from fp.fp import FreeProxy
from time import sleep
import re
import aiohttp
import os

try:
    from routers.parsing.parsing_config import VOID_TEXT_CHAR
    VOID_CHAR = VOID_TEXT_CHAR
except:
    VOID_CHAR = ''

MAX_POLL_ANWSER_LEN = 100 # Максимальная длинна строки ответа. Ограничения телеграмм 100

def setup_logger(logger_name, log_file, level=logging.INFO, mode = 'w'):
    """To setup as many loggers as you want"""
    formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s', datefmt='%d.%m.%Y %H:%M:%S')
    handler = logging.FileHandler(log_file, mode)
    handler.setFormatter(formatter)
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    logger.addHandler(handler)
    return logger

class Parser(ParserInterface):
    name = 'ВКонтакте'
    description = 'Парсер стен пользователей и сообществ социальной сети ВКонтакте'
    file = os.path.abspath(__file__)
    loger = setup_logger('VKParser', 'VKParser.log', level=logging.INFO, mode='w')

    @classmethod
    async def parse(cls, params: ParseParams, session: aiohttp.ClientSession = None):
        # Полуаем стену из Вконтакте
        json_data, next_from = await cls.get_vk_wall(params=params, session=session)
        if json_data != None:
            pass
        else:
            return ParserInterfaceReturns.GetVKWallError
        # Преобразовываем данные в стандартный формат и отправляем в исполнителю
        result = await cls.normalize_data(json_data, params)
        return result


    @classmethod
    async def get_entries_count(cls, params: ParseParams):
        res = 0
        group_info, next_from = await cls.get_vk_wall(params=params)
        if type(group_info) is not ParserInterfaceReturns:
            try:
                res = group_info['response']['count']
            except:
                pass
        else:
            res = group_info
        return res



    @classmethod
    async def get_vk_wall(cls, params: ParseParams, session=None):
        '''
        Получение записей со стены, используя внутренее API ВК
        Возвращает два параметра
        '''
        try:
            target_id = int(params.target_id)
            if params.target_type == 'user':
                if target_id < 0: target_id = - target_id
            else:
                if target_id > 0: target_id = - target_id
        except:
            cls.loger.error(f'get_vk_wall. Неправильное значение target_id - {params.target_id}')
            return ParserInterfaceReturns.GetVKWallError, 0
        try:
            proxie_not_got = True
            proxies = {}
            proxy_str = ''
            px_tries = 0
            if params.use_free_proxy:
                while proxie_not_got:
                    try:
                        proxy_obj = FreeProxy(anonym=True, https=True).get()
                        proxie_not_got = False
                        proxies = {
                            "https": proxy_obj,
                        }
                    except:
                        px_tries += 1
                        if px_tries < 10:
                            pass
                            #print('Доступные прокси отсутствуют. Ждем.')
                        else:
                            #print('Обновление не удалось, доступные прокси отсутствуют.')
                            cls.loger.warning('Обновление не удалось, доступные прокси отсутствуют.')
                            return ParserInterfaceReturns.NoFreeProxy, 0
                        sleep(30)
            if params.proxy_url != '' and params.proxy_protocol != '':
                proxies = {
                    f'{params.proxy_protocol}': params.proxy_url,
                }
                proxy_str = f'{params.proxy_protocol}: params.proxy_url'
            url = f"https://api.vk.com/method/wall.get?owner_id={target_id}&offset={params.offset}&count={params.post_count}&filter={params.filter}&access_token={params.token}&v=5.131"
            ua = UserAgent()
            header = {'User-Agent': str(ua.random)}
            if session == None:
                conn = aiohttp.TCPConnector(limit=None, ttl_dns_cache=300)
                async with aiohttp.ClientSession(connector=conn) as new_session:
                    req = await new_session.get(url, headers=header, proxy=proxy_str, ssl=False)
                    if req.status != 200:
                        # error = service_func.check_error_code_in_json(req)
                        cls.loger.error(
                            f'Парсер: VKParser (target_id={target_id}, filter={params.filter}) ошибка парсинга:'
                            f' код requests - {req.status_code}')
                        return ParserInterfaceReturns.GetVKWallError, 0
                    else:
                        res = await req.json()
            else:
                req = await session.get(url, headers=header, proxy=proxy_str, ssl=False)
                if req.status != 200:
                    # error = service_func.check_error_code_in_json(req)
                    cls.loger.error(
                        f'Парсер: VKParser (target_id={target_id}, filter={params.filter}) ошибка парсинга:'
                        f' код requests - {req.status_code}')
                    return ParserInterfaceReturns.GetVKWallError, 0
                else:
                    res = await req.json()
            try:
                offset = int(res['response']['next_from'])
            except:
                offset = 0
            return res, offset
        except Exception as ex:
            cls.loger.error(
                f'Парсер VKParser (target_id={target_id}, filter={params.filter}) ошибка парсинга: {ex}')
            return ParserInterfaceReturns.PyError


    @classmethod
    async def normalize_data(cls, json_data, params: ParseParams) -> Union[list[APost], ParserInterfaceReturns]:
        '''
        Приводит спарсеные данные в стандартизированную форму
        :param json_data:
        :param task_id:
        :return:
        '''
        try:
            res = []
            if "response" not in json_data:
                # Пытаемся получить описание ошибки
                try:
                    vk_err = json_data['error']['error_msg']
                except Exception as ex:
                    vk_err = 'Не определено'
                err_str = f'Ошибка при выполнении normalize_data(task_key={params.target_id}): "в данных нет ключа [response]". VK_error: {vk_err}'
                cls.loger.error(err_str)
                return ParserInterfaceReturns.NormalizeDataError
            # Просматриваем все посты
            post_num = 0
            for i, post in enumerate(json_data['response']['items']):
                try:  # Если закрепленный пост то пропускаем его
                    pinned = post['is_pinned']
                    if pinned == True:
                        continue
                except:
                    try:
                        post_id = post['id']
                        try:
                            text = post['text']
                            text = text.strip()
                            text = await cls.__del_forbiden_tg_char(text)
                        except:
                            text = VOID_CHAR
                        try:
                            post_datetime = post['date']
                        except:
                            post_datetime = 0
                        try:
                            views_count = post['views']['count']
                        except:
                            views_count = 0
                        try:
                            likes_count = post['likes']['count']
                        except:
                            likes_count = 0
                        try:  # Если репост
                            repost_text = post['copy_history'][0]['text']
                            repost_text = await cls.__del_forbiden_tg_char(repost_text)
                            text = str(text) + str(repost_text)
                            post = post['copy_history'][0]
                        except Exception as ex:
                            pass
                        if text == '': text = VOID_CHAR
                        hashtags = await cls.__get_hashtags(text)
                        #
                        post_src = APost(post_id, text, views_count, likes_count, post_datetime, hashtags=hashtags)
                        # Работаем с медиафайлами
                        if "attachments" in post:
                            attachments = post["attachments"]
                            audio_i = 0
                            poll_i = 0
                            for src in attachments:
                                if 'type' in src:
                                    match src['type']:
                                        case 'poll':
                                            try:
                                                question = src['poll']['question']
                                                answers = src['poll']['answers']
                                                answer_str = ''
                                                for answer in answers:
                                                    anws_text = answer['text']
                                                    anws_text = anws_text[0:MAX_POLL_ANWSER_LEN - 1]
                                                    answer_str = answer_str + f"{anws_text}|| "
                                                answer_str = answer_str[0:len(answer_str) - 3]
                                                anonymous = src['poll']['anonymous']
                                                multiple = src['poll']['multiple']
                                                try:
                                                    poll_photo = src['poll']['photo']['images'][0]['url']
                                                    # poll_photo=get_clear_url(poll_photo)
                                                    # photo = content_dm.Photo.create(owner=post_odj, url=poll_photo)
                                                    photo = {}
                                                    photo['url'] = poll_photo
                                                    photo['caption'] = ''
                                                    post_src.photos.append(photo)
                                                except:
                                                    pass
                                                poll = {}
                                                poll['question'] = question
                                                poll['answers'] = answer_str
                                                poll['anonymous'] = anonymous
                                                poll['multiple'] = multiple
                                                post_src.polls.append(poll)
                                                poll_i += 1
                                            except Exception as ex:
                                                cls.loger.error(f'Ошибка при нормализации опроса. Цель: {params.target_id}. Ошибка: {ex}')
                                        case 'photo':
                                            try:
                                                max_size = len(src['photo']['sizes']) - 1
                                            except:
                                                max_size = 0
                                            if max_size < 0: max_size = 0
                                            photo_text = src['photo']['text']
                                            photo = {}
                                            photo['url'] = src['photo']['sizes'][max_size]['url']
                                            photo['caption'] = photo_text
                                            post_src.photos.append(photo)
                                        case 'link':
                                            try:
                                                try:
                                                    max_size = len(src['link']['photo']['sizes']) - 1
                                                except:
                                                    max_size = 0
                                                if max_size < 0: max_size = 0
                                                photo_text = src['link']['photo']['text']
                                                photo = {}
                                                photo['url'] = src['link']['photo']['sizes'][max_size]['url']
                                                photo['caption'] = photo_text
                                                post_src.photos.append(photo)
                                            except:
                                                pass
                                            try:
                                                link = {}
                                                link['description'] = src['link']['description']
                                                link['title'] = src['link']['title']
                                                link['url'] =  src['link']['url']
                                                post_src.links.append(link)
                                            except:
                                                pass
                                        case 'audio':
                                            audio_url = src['audio']['url']
                                            audio_title = await cls.__del_forbiden_tg_char(src['audio']['title'])
                                            audio_artist = await cls.__del_forbiden_tg_char(src['audio']['artist'])
                                            audio_title = await cls.__clear_file_name(audio_title)
                                            audio_artist = await cls.__clear_file_name(audio_artist)
                                            audio = {}
                                            audio['artist'] = audio_artist
                                            audio['title'] = audio_title
                                            audio['url'] = audio_url
                                            post_src.audios.append(audio)
                                            audio_i = audio_i + 1
                                        case 'video':
                                            att_video = src['video']
                                            video_description = ''
                                            # формируем данные для составления запроса на получение ссылки на видео
                                            try:
                                                video_post_id = att_video["id"]
                                                video_owner_id = att_video["owner_id"]
                                            except:
                                                continue
                                            try:
                                                video_title = att_video["title"]
                                                video_title = await cls.__del_forbiden_tg_char(video_title)
                                                video_title =await cls.__clear_file_name(video_title)
                                                if (video_title == "Видео недоступно") or (
                                                        'content_restricted' in att_video):
                                                    # Если Вконтакте ограничевает доступ к видео пытаемся сформировать на него прямую ссылку
                                                    video_title = ''
                                                    video_url = f'https://vk.com/video{video_owner_id}_{video_post_id}'
                                                    try:
                                                        video_description = att_video["description"]
                                                        video_description = await cls.__del_forbiden_tg_char(video_description)
                                                        #video_title = video_title + '. ' + video_description
                                                    except:
                                                        pass
                                                    # video = content_dm.Video.create(owner=post_odj, title=video_title, url=video_url)
                                                    video = {}
                                                    video['title'] = video_title
                                                    video['description'] = video_description
                                                    video['url'] = video_url
                                                    post_src.videos.append(video)
                                                    # videos.append([video_title, video_url])
                                                    continue
                                            except:
                                                video_title = ''
                                            try:
                                                video_description = att_video["description"]
                                                video_description = await cls.__del_forbiden_tg_char(video_description)
                                                #video_title = video_title + '. ' + video_description
                                            except:
                                                pass
                                            try:
                                                video_access_key = att_video["access_key"]
                                            except:
                                                # video_access_key = att_video["track_code"]
                                                video_url = f'https://vk.com/video{video_owner_id}_{video_post_id}'
                                                # video = content_dm.Video.create(owner=post_odj, title=video_title, url=video_url)
                                                # videos.append([video_title, video_url])
                                                video = {}
                                                video['title'] = video_title
                                                video['description'] = video_description
                                                video['url'] = video_url
                                                post_src.videos.append(video)
                                                continue
                                            video_get_url = f"https://api.vk.com/method/video.get?videos={video_owner_id}_{video_post_id}_{video_access_key}&extended=1&access_token={params.token}&v=5.131"
                                            #v_req = requests.get(video_get_url)
                                            conn = aiohttp.TCPConnector(limit=None, ttl_dns_cache=300)
                                            async with aiohttp.ClientSession(connector=conn) as new_session:
                                                v_req = await new_session.get(video_get_url, ssl=False)
                                                v_res = await v_req.json()
                                            try:
                                                video_url = v_res["response"]["items"][0]["player"]
                                            except:
                                                # Пытаемся на всякий случай с резервным токеном
                                                video_get_url = f"https://api.vk.com/method/video.get?videos={video_owner_id}_{video_post_id}_{video_access_key}&access_token={params.token}&v=5.131"
                                                #v_req = requests.get(video_get_url)
                                                conn = aiohttp.TCPConnector(limit=None, ttl_dns_cache=300)
                                                async with aiohttp.ClientSession(connector=conn) as new_session:
                                                    v_req = await new_session.get(video_get_url, ssl=False)
                                                    v_res = await v_req.json()
                                                try:
                                                    video_url = v_res["response"]["items"][0]["player"]
                                                except:
                                                    # Если всеравно не получилось пропускаем
                                                    continue
                                            # Оцениваем плеер для вывода ссылки с предпросмотром
                                            # Если плеер вконтакте меняем ссылку на вновьсформированую
                                            is_vk = video_url.find('vk.com')
                                            if is_vk != -1:
                                                # Это внутреннее видео ВКонтакте делаем ссылку с предпросмотром
                                                # player_url=f'<a href="{video_url}">[Смотреть]</a>'
                                                video_url_res = f'https://vk.com/video{video_owner_id}_{video_post_id}'
                                                # videos.append([video_title, video_url])
                                                # videos.append(['', video_url_res])
                                                # video = content_dm.Video.create(owner=post_odj, title=video_title, url=video_url_res)
                                                video = {}
                                                # Определяем можно ли репостить видео
                                                try:
                                                    can_repost = v_res["response"]["items"][0]["can_repost"]
                                                except:
                                                    can_repost = 0
                                                video['title'] = video_title
                                                if can_repost == 1:
                                                    video['url'] = video_url_res
                                                else:
                                                    video['url'] = video_url
                                                video['description'] = video_description
                                                post_src.videos.append(video)
                                            else:
                                                # Проверяем если ютуб то удаляем мусор из ссылки
                                                is_yt = video_url.find('embed')
                                                if is_yt != -1:
                                                    video_url =await cls.__get_clear_url(video_url)
                                                    video_url = video_url.replace('embed/', 'watch?v=')
                                                # videos.append([video_title, video_url])
                                                # video = content_dm.Video.create(owner=post_odj, title=video_title, url=video_url)
                                                video = {}
                                                video['title'] = video_title
                                                video['url'] = video_url
                                                video['description'] = video_description
                                                post_src.videos.append(video)
                                        case 'doc':
                                            # docs.append(src['doc']['url'])
                                            # doc = content_dm.Doc.create(owner=post_odj, url=src['doc']['url'])
                                            doc = {}
                                            doc['url'] = src['doc']['url']
                                            post_src.docs.append(doc)
                        res.append(post_src)
                        post_num = post_num + 1
                    except Exception as ex:
                        cls.loger.error(f'Ошибка нормализации данных. Цель: {params.target_id}. Номер поста: {post_num}. Ошибка: {ex}')
                        continue
            return res
        except Exception as ex:
            cls.loger.error(f'Ошибка нормализации данных. Цель: {params.target_id}. Ошибка: {ex}')
            return ParserInterfaceReturns.NormalizeDataError

    @classmethod
    async def __del_forbiden_tg_char(cls, oldstr: str):
        newstr = oldstr.replace("'", "")
        newstr = newstr.replace("|", "")
        newstr = newstr.replace(">", "")
        newstr = newstr.replace("<", "")
        return newstr

    @classmethod
    async def __get_hashtags(cls, text: str) -> list:
        pat = re.compile(r"#(\w+)")
        res = pat.findall(text)
        # Понижаем регистр
        res = [x.lower() for x in res]
        return res

    @classmethod
    async def __clear_file_name(cls, name: str):
        name = name.strip()
        name = name.replace("'", "")
        name = name.replace('"', "")
        name = name.replace("!", "")
        name = name.replace("?", "")
        name = name.replace("/", "")
        name = name.replace("|", "")
        name = name.replace("^", "")
        name = name.replace("@", "")
        name = name.replace("#", "")
        name = name.replace("№", "")
        name = name.replace(";", "")
        name = name.replace("$", "")
        name = name.replace("%", "")
        name = name.replace(":", "")
        name = name.replace("&", "")
        name = name.replace("*", "")
        return name

    @classmethod
    async def __get_clear_url(cls, url: str):
        ind = url.find('?')
        if ind == -1:
            return url
        else:
            return url[0:ind]

    # @classmethod
    # def get_vk_wall(cls, params: ParseParams):
    #     '''
    #     Получение записей со стены, используя внутренее API ВК
    #     '''
    #     try:
    #         url = f"https://api.vk.com/method/wall.get?owner_id={params.target_id}&offset={params.offset}&count={params.post_count}&filter={filter}&access_token={cls.token}&v=5.131"
    #         ua = UserAgent()
    #         header = {'User-Agent': str(ua.random)}
    #         req = requests.get(url, headers=header)
    #         if req.status_code != 200:
    #             url = f"https://api.vk.com/method/wall.get?owner_id={params.target_id}&offset={params.offset}&count={params.post_count}&filter={filter}&access_token={cls.reserve_token}&v=5.131"
    #             req = requests.get(url, headers=header)
    #         # print(req.text)
    #         if req.status_code != 200:
    #             # error = service_func.check_error_code_in_json(req)
    #             cls.loger.error(
    #                 f'Парсер: VKParser (target_id={params.target_id}, filter={filter}) ошибка парсинга:'
    #                 f' код requests - {req.status_code}')
    #             return None
    #         else:
    #             return req.json()
    #     except Exception as ex:
    #         cls.loger.error(
    #             f'Парсер VKParser (target_id={params.target_id}, filter={filter}) ошибка парсинга: {ex}')
    #         return None

    @classmethod
    async def get_vk_object_id(cls, vk_object_name: str, token: str, with_type = False):
        urls = []
        urls.append(
            f"https://api.vk.com/method/utils.resolveScreenName?screen_name={vk_object_name}&access_token={token}&v=5.131")
        urls.append(
            f"https://api.vk.com/method/utils.resolveScreenName?screen_name={vk_object_name}&access_token={token}&v=5.131")
        ua = UserAgent()
        header = {'User-Agent': str(ua.random)}
        for url in urls:
            #page = requests.get(url, headers=header)
            conn = aiohttp.TCPConnector(limit=None, ttl_dns_cache=300)
            async with aiohttp.ClientSession(connector=conn) as new_session:
                page = await new_session.get(url, headers=header, ssl=False)
                res = await page.json()
            try:
                vk_group_id = res['response']['object_id']
                vk_type = res['response']['type']
                if with_type:
                    return int(vk_group_id), vk_type
                else:
                    return int(vk_group_id)
            except:
                try:
                    err_str = res['error']['error_msg']
                    if with_type:
                        return err_str, 'ошибка'
                    else:
                        return err_str
                except Exception as ex:
                    return None
                # Если ошибка пробуем с резервным токеном
        return None

    @classmethod
    async def get_vk_group_info(cls, vk_group_id, token):
        urls = []
        urls.append(
            f"https://api.vk.com/method/groups.getById?group_id={vk_group_id}&fields=description,members_count&access_token={token}&v=5.131")
        urls.append(
            f"https://api.vk.com/method/groups.getById?group_id={vk_group_id}&fields=description,members_count&access_token={token}&v=5.131")
        ua = UserAgent()
        header = {'User-Agent': str(ua.random)}
        for url in urls:
            #req_gr_info = requests.get(url, headers=header)
            #gr_info = req_gr_info.json()
            conn = aiohttp.TCPConnector(limit=None, ttl_dns_cache=300)
            async with aiohttp.ClientSession(connector=conn) as new_session:
                req_gr_info = await new_session.get(url, headers=header, ssl=False)
                gr_info = await req_gr_info.json()
            try:
                res={}
                res['name'] = gr_info['response'][0]['name']
                res['description'] = gr_info['response'][0]['description']
                res['members_count'] = gr_info['response'][0]['members_count']
                return res
            except:
                continue
        return None

    @classmethod
    async def get_vk_user_info(cls, vk_user_id, token):
        urls = []
        urls.append(
            f"https://api.vk.com/method/users.get?user_ids={vk_user_id}&access_token={token}&v=5.131")
        urls.append(
            f"https://api.vk.com/method/users.get?user_ids={vk_user_id}&access_token={token}&v=5.131")
        ua = UserAgent()
        header = {'User-Agent': str(ua.random)}
        for url in urls:
            #req_user_info = requests.get(url, headers=header)
            #user_info = req_user_info.json()
            conn = aiohttp.TCPConnector(limit=None, ttl_dns_cache=300)
            async with aiohttp.ClientSession(connector=conn) as new_session:
                req_user_info = await new_session.get(url, headers=header, ssl=False)
                user_info = await req_user_info.json()
            try:
                res={}
                res['first_name'] = user_info['response'][0]['first_name']
                res['last_name'] = user_info['response'][0]['last_name']
                res['full_name'] = res['first_name'] + ' ' + res['last_name']
                return res
            except:
                continue
        return None

    @classmethod
    async def get_vk_user_group(cls, vk_user_id, token, filter):
        '''
        Возвращает список групп пользователя в которых он состоит, можно получить где он админ
        :param vk_user_id: мой 82310753
        :param token:
        :param filter: При указании фильтра hasAddress вернутся сообщества, в которых указаны адреса в соответствующем блоке,
        admin будут возвращены сообщества, в которых пользователь является администратором, editor — администратором или редактором,
        moder — администратором, редактором или модератором, advertiser — рекламодателем. Если передано несколько фильтров,
        то их результат объединяется.
        :return:
        '''
        urls = []
        urls.append(
            f"https://api.vk.com/method/groups.get?user_id={vk_user_id}&access_token={token}&filter={filter}&v=5.199")
        urls.append(
            f"https://api.vk.com/method/groups.get?user_id={vk_user_id}&access_token={token}&filter={filter}&v=5.131")
        ua = UserAgent()
        header = {'User-Agent': str(ua.random)}
        for url in urls:
            try:
                #req_user_info = requests.get(url, headers=header)
                #user_info = req_user_info.json()
                conn = aiohttp.TCPConnector(limit=None, ttl_dns_cache=300)
                async with aiohttp.ClientSession(connector=conn) as new_session:
                    req_user_info = await new_session.get(url, headers=header, ssl=False)
                    user_info = await req_user_info.json()
                return user_info
            except:
                continue
        return None