'''Этот модуль содержит глобальные объекты - логеры'''

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

dialogs_loger = setup_logger('DlgLoger', 'dlgs_log.log')