'''Этот модуль содержит глобальные объекты - логеры для внутренних механник:
ботов, консоли, парсинга, публикации'''

import logging
import os
from main_config import MAIN_PATH

LOGS_PATH = MAIN_PATH +'\\logs\\' # путь к логам

if not os.path.isdir(LOGS_PATH):
    try:
        os.mkdir(LOGS_PATH)
    except Exception as ex:
        print(f'Создать папку для логов "logs" не удалось. Причина: {ex}')

def setup_logger(logger_name, log_file, level=logging.INFO, mode = 'w'):
    """To setup as many loggers as you want"""
    logging.basicConfig(filename=log_file,
                        format='%(asctime)s %(levelname)-8s %(message)s', datefmt='%d.%m.%Y %H:%M:%S',
                        filemode=mode,
                        level=level)
    formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s', datefmt='%d.%m.%Y %H:%M:%S')
    handler = logging.FileHandler(f'{log_file}', mode)
    handler.setFormatter(formatter)
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    logger.addHandler(handler)
    return logger

app_loger = setup_logger('AppLoger', f'{LOGS_PATH}\\log.log') # логер приложения
bots_loger = setup_logger('BotsLoger', f'{LOGS_PATH}\\bots.log') # логер ботов
parsers_loger = setup_logger('ParsersLoger', f'{LOGS_PATH}\\parsers.log') # логер парсинга
publicators_loger = setup_logger('PublicatorsLoger', f'{LOGS_PATH}\\publicators.log') # логер публикаторов
telegram_loger = setup_logger('TelegramLoger', f'{LOGS_PATH}\\telegram.log') # логер ошибок телеграма, обычно проблемы со связью
dialogs_loger = setup_logger('DlgLoger', f'{LOGS_PATH}\\dlgs_log.log') # логер диалогов представлений