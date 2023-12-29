import logging
import importlib
import os
import inspect
import time
from datetime import date
import enum

#
from routers.parsing.interface_parser import ParserInterface

# Проверяем наличие файла конфигурации
config_file = os.path.dirname(os.path.abspath(__file__)) + f'\\parsing_config.py'
if not os.path.isfile(config_file):
    print('Ошибка загрузки приложения: отсутствует файл конфигурации parsing_config.py')
    raise 'Критическая ошибка!!!'
else:
    from routers.parsing.parsing_config import ROUTERS_DIR, ROUTER_DIR, PARSERS_DIR


class ParserDispatcherErrors(enum.Enum):
    Good = 'в норме'
    NoConfig = 'настройка не выполнена'
    NoParsers = 'парсеры не найдены'


class ParserDispatcher:
    '''Объект диспетчера парсеров'''
    def __init__(self, logger: logging.Logger):
        '''При создании диспетчера он подгружает все парсеры, найденые в папке из конфига'''
        #
        self.logger = logger
        self.logger.info('Создание диспетчера парсеров...')
        self.status = ParserDispatcherErrors.Good
        # Создаём движки парсеров
        self.parsers = []
        # Проверяем директорию
        parsers_path = os.path.dirname(os.path.abspath(__file__)) + f'\\parsers\\'
        if not os.path.isdir(parsers_path):
            self.status = ParserDispatcherErrors.NoParsers
            self.logger.critical(
                'Невозможно создать диспетчер парсеров: отсутствует директория с парсерами parsers')
            self.logger.info(f'Создание диспетчера парсеров прервано.')
            return
        # Получаем список файлов в папке парсеров
        parsers_files = os.listdir(parsers_path)
        # Пробуем подключить парсеры
        for parser_file in parsers_files:
            try:
                pos = parser_file.find('.py')
                if pos == -1:
                    continue
                else:
                    parser_file = parser_file[:pos]
                command_module = importlib.import_module(f'{ROUTERS_DIR}.{ROUTER_DIR}.{PARSERS_DIR}.{parser_file}')
                # Проверяем модуль на предмет наличия там класса MainParser
                cur_parser_class = None
                try:
                    members = inspect.getmembers(command_module)
                    module_classes = []
                    available_parsers = []
                    for name, obj in members:
                        if inspect.isclass(obj):
                            #module_classes.append(obj)
                            if issubclass(obj, ParserInterface) and obj is not ParserInterface:
                                available_parsers.append(obj)
                                cur_parser_class = obj
                    # if MainParser not in module_classes:
                    #     continue
                    pass
                finally:
                    # Добавляем парсер в список парсеров
                    if cur_parser_class != None:
                        self.parsers.append(cur_parser_class)
                #command_module = importlib.import_module(f'parsers.vk_parser')
                #command_module.run()
            except Exception as ex:
                self.logger.error(f'Ошибка загрузки парсера "{parser_file}": {ex}')
        self.parsers_name_list = []
        for parser_cl in self.parsers:
            self.parsers_name_list.append(parser_cl.name)
        info_str = f'Диспетчер парсеров создан. Статус: {self.status.value}. Загружены следующие парсеры: {self.parsers_name_list}'
        self.logger.info(info_str)
        print(info_str)

    def get_parser(self, name):
        for el in self.parsers:
            if el.name == name:
                return el
        return None