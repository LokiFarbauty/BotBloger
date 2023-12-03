# routers
from routers.console.terminal_interface import Command
from routers.dispatcher import parsing_dispatcher
from routers.parsing.interface_parser import ParserInterface, ParseParams
from routers.analyzer import analyze_posts, AnalyzerParams

commands = []

# commands.append(
#      Command(name='get_users', func=User.get_users_obj, args_num=1, help='Получить пользователей из базы данных. Параметры: 1 - user_id либо username.')
# )

def vk_parse(target_id=0, token='test'):
    if token == 'test':
        token = 'vk1.a.fZyiWIVGGg_7sM0euOzteiauES3ZM2DP73QXvWnMaAR2lc7-ww2bms3zWifrqKDTTeUAkW06-sEAiHJLxZwKcTlZaQD-q_EQZatNZOK_XTXp7Y3FVMqi6THV29qM96AIDfNmEMR3Fkg1rNTnObyCqbn9wQmsbWsCBSmYHflU9cOyy-Dc4i1g1QdiWQxmKiPrTu7hicXNU-3TrVvzrLIXSA'
    params = ParseParams(target_id=target_id, token=token, post_count=10, use_free_proxy=False)
    parser = parsing_dispatcher.get_parser('ВКонтакте')
    if parser != None:
        parse_res=parser.parse(params)
    else:
        return 'Парсер не найден'
    # Анализ
    #
    params = AnalyzerParams(hashtags=['паста'], min_text_len=10)
    proc_posts = analyze_posts(parse_res, params)
    #
    res = []
    for rec in proc_posts:
       res.append(rec.text)
    return res

commands.append(
     Command(name='vk_parse', func=vk_parse, args_num=1, help='Получить данные со стены страницы ВКонтакте. Параметры: 1 - target_id (id объекта ВК)')
)

def get_vk_post_count(target_id=0, token='test'):
    if token == 'test':
        token = 'vk1.a.fZyiWIVGGg_7sM0euOzteiauES3ZM2DP73QXvWnMaAR2lc7-ww2bms3zWifrqKDTTeUAkW06-sEAiHJLxZwKcTlZaQD-q_EQZatNZOK_XTXp7Y3FVMqi6THV29qM96AIDfNmEMR3Fkg1rNTnObyCqbn9wQmsbWsCBSmYHflU9cOyy-Dc4i1g1QdiWQxmKiPrTu7hicXNU-3TrVvzrLIXSA'
    params = ParseParams(target_id=target_id, token=token, post_count=1, use_free_proxy=False)
    parser = parsing_dispatcher.get_parser('ВКонтакте')
    if parser != None:
        res=parser.get_entries_count(params)
    else:
        return 'Парсер не найден'
    return res

commands.append(
     Command(name='get_vk_post_count', func=get_vk_post_count, args_num=1, help='Получить количество записей на стене страницы ВКонтакте. Параметры: 1 - target_id (id объекта ВК)')
)