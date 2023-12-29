'''Этот модуль содержит глобальные объекты - логеры для внутренних механник:
ботов, консоли, парсинга, публикации'''

import logging

def setup_logger(logger_name, log_file, level=logging.INFO, mode = 'w'):
    """To setup as many loggers as you want"""
    formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s', datefmt='%d.%m.%Y %H:%M:%S')
    handler = logging.FileHandler(log_file, mode)
    handler.setFormatter(formatter)
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    logger.addHandler(handler)
    return logger

app_loger = setup_logger('AppLoger', 'log.log') # логер приложения
bots_loger = setup_logger('BotsLoger', 'bots.log') # логер ботов
parsers_loger = setup_logger('ParsersLoger', 'parsers.log') # логер парсинга
publicators_loger = setup_logger('PublicatorsLoger', 'publicators.log') # логер публикаторов