'''Этот модуль содержит глобальные объекты - диспетчер парсеров.
Он отвечает за автоматическую подгрузку парсеров из папки parsers.
Парсеры подгружаются при создании объекта ParserDispatcher и дальше хранятся в нем'''

import logging
import importlib
import os
import inspect
import time
from datetime import date
import enum
import asyncio
#
# models
from models.data_model import get_elements
from models.data.parse_task import ParseTask, ParseTaskStates, ParseTaskActive
# routers
from routers.logers import parsers_loger, app_loger
from routers.parsing.interface_parser import ParserInterface, ParseParams
from routers.parsing.parsing import parsing, INFINITE


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

class ASTaskStatus(enum.Enum):
    Done = 'выполнена'
    Cancelled = 'остановлена'
    Active = 'выполняется'
    NotFound = 'не найдена'

class ParserDispatcher:
    '''Объект диспетчера парсеров'''
    def __init__(self, logger: logging.Logger):
        '''При создании диспетчера он подгружает все парсеры, найденые в папке из конфига'''
        #
        # Текущие задачи
        self.tasks = []
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

    def get_parser(self, name) -> ParserInterface:
        for el in self.parsers:
            if el.name == name:
                return el
        return None

    def get_task_process(self, task_name: str):
        res = None
        try:
            for tp in self.tasks:
                tp_name = tp.get_name()
                if task_name == tp_name:
                    res = tp
        except Exception as ex:
            res = None
        return res

    def get_task_status(self, taskname: str):
        # Получаем статус задачи
        task_process = self.get_task_process(taskname)
        if task_process == None:
            return ASTaskStatus.NotFound
        if task_process.done():
            return ASTaskStatus.Done
        if task_process.cancelled():
            return ASTaskStatus.Cancelled
        return ASTaskStatus.Active

    def stop_task(self, taskname: str):
        # Получаем задачу
        try:
            task_status = self.get_task_status(taskname)
            if task_status == ASTaskStatus.Active:
                tp = self.get_task_process(taskname)
                if tp != None:
                    tp.cancel()
                    task = ParseTask.get_task(name=taskname)
                    if task != None:
                        task.state = ParseTaskStates.Stopped.value
                        task.save()
                    return f'Задача "{taskname}" остановлена.'
                else:
                    return f'Задача "{taskname}" не найдена.'
            else:
                return f'Задача "{taskname}" не была активной.'
        except Exception as ex:
            return ex

    async def start_task(self, task_key = 0, taskname: str = '', func=None):
        # func - функция парсинга
        # Получаем задачу
        _kwargs = {}
        try:
            if task_key == 0:
                task = ParseTask.get_task(name=taskname)
            else:
                task = ParseTask.get_by_id(task_key)
            if task == None:
                return f'Задача "{taskname}" не найдена в базе.'
            else:
                task.state = ParseTaskStates.InWork.value
                task.save()
            task_process = self.get_task_process(taskname)
            _kwargs['task'] = task
            _kwargs['infinite_def'] = INFINITE
            _kwargs['parser'] = self.get_parser(task.parser.platform)
            if task_process == None:
                _kwargs['quick_start'] = True
                #self.tasks.append(asyncio.create_task(func(task, quick_start=True), name=taskname))
                self.tasks.append(asyncio.create_task(func(**_kwargs), name=taskname))
                return f'Задача "{taskname}" запущена.'
            else:
                task_status = self.get_task_status(taskname)
                if task_status == ASTaskStatus.Active:
                    return f'Задача "{taskname}" уже запущена.'
                else:
                    self.tasks.remove(task_process)
                    _kwargs['quick_start'] = False
                    #self.tasks.append(asyncio.create_task(func(task), name=taskname))
                    self.tasks.append(asyncio.create_task(func(**_kwargs), name=taskname))
                    return f'Задача "{taskname}" запущена.'
        except Exception as ex:
            return f'Запуск задачи "{taskname}" не удался, причина: {ex}'

    async def init_tasks(self):
        # Получаем список задач из базы
        print(f'Запуск задач...')
        app_loger.info(f'Запуск задач...')
        tasks = get_elements(ParseTask)
        task_num = 0
        _kwargs = {}
        for task in tasks:
            # Настраиваем
            try:
                if task.active == ParseTaskActive.InWork.value:
                    _kwargs['task'] = task
                    _kwargs['infinite_def'] = INFINITE
                    _kwargs['parser'] = self.get_parser(task.parser.platform)
                    _kwargs['quick_start'] = False
                    self.tasks.append(asyncio.create_task(parsing(**_kwargs), name=task.name))
                    app_loger.info(f'Запущена задача <{task.name}>.')
                    print(f'Запущена задача <{task.name}>.')
                    task_num += 1
            except Exception as ex:
                # print(f'При запуске задачи {task.name} (key: {task.get_id()}) возникла ошибка: {ex}')
                parsers_loger.error(f'При запуске задачи {task.name} (key: {task.get_id()}) возникла ошибка: {ex}')
                continue
        print(f'Запущено {task_num} задач.')
        app_loger.info(f'Запущено {task_num} задач.')
        # print(f'Запущено {task_num} задач.')
        return 0


parsers_dispatcher = ParserDispatcher(parsers_loger)

