import os

MAIN_PATH = os.path.dirname(os.path.abspath(__file__)) # путь к файлу запуска
DOWNLOADS_PATH = f'{MAIN_PATH}\\downloads'

if not os.path.isdir(DOWNLOADS_PATH):
    try:
        os.mkdir(DOWNLOADS_PATH)
    except Exception as ex:
        print(f'Создать папку для скачиваний не удалось. Причина: {ex}')