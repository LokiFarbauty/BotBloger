'''Конфигурационный файл для парсинга'''

import os

ROUTERS_DIR = 'routers'
ROUTER_DIR = 'parsing'
PARSERS_DIR = 'parsers' # папка в которой хранятся парсеры
PARSERS_PATH = os.path.dirname(os.path.abspath(__file__))+f'\\{PARSERS_DIR}\\' # путь к файлам парсеров
