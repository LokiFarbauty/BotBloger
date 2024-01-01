'''Конфигурационный файл для парсинга'''

import os

ROUTERS_DIR = 'routers'
ROUTER_DIR = 'parsing'
PARSERS_DIR = 'parsers' # папка в которой хранятся парсеры
PARSERS_PATH = os.path.dirname(os.path.abspath(__file__))+f'\\{PARSERS_DIR}\\' # путь к файлам парсеров
PARSE_VK_POST_NUM = 50 # Количество постов которое получаем используя ВК api за раз
PARSE_VK_MAX_TEXT_LEN = 50000 # Максимальная длинна текста, когда ничего не указано пользователем
VOID_TEXT_CHAR = '' # Этим заполняется пустой текст

