
'''Конфигурационный файл балы данных.
При импорте создает каталог DB_PATH
База данных одна для всех задач, от принципа множественных БД решено отказаться'''


import os
from playhouse.sqlite_ext import SqliteExtDatabase

DB_PATH = os.path.dirname(os.path.abspath(__file__))+'\\dbs\\' # путь к файлу базы данных
DBM_MODELS_DIR = 'models'
DBM_DATA_DIR = 'data'
DBM_DATA_PATH = os.path.dirname(os.path.abspath(__file__))+f'\\{DBM_DATA_DIR}\\' # путь к моделям данных
DB_FILE_NAME = 'vksync.db' # файл базы данных
DB_FILE_PATH = DB_PATH + DB_FILE_NAME # путь к файлу базы данных

db = SqliteExtDatabase(DB_FILE_PATH, pragmas=(
    ('cache_size', -1024 * 64),  # 64MB page-cache.
    ('journal_mode', 'wal'),  # Use WAL-mode (you should always use this!).
    ('foreign_keys', 1)))

if not os.path.isdir(DB_PATH):
    try:
        os.mkdir(DB_PATH)
    except Exception as ex:
        print(f'Создать папку для базы данных "dbs" не удалось. Причина: {ex}')


