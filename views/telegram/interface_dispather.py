import os
import importlib
import inspect
#
from views.telegram.interface_pattern import BotViewInterface
from routers.logers import app_loger
#



current_path = os.path.dirname(os.path.abspath(__file__)) # путь к файлу
py_path = 'views.telegram'

def load_bot_interfaces():
    try:
        # Подгружаем все найденые интерфейсы
        print(f'Загрузка интерфейсов...')
        app_loger.info(f'Загрузка интерфейсов...')
        interfaces_lst = []
        interfaces_class_lst = []
        # проверяем директорию
        if not os.path.isdir(current_path):
            print(f'Невозможно получить интерфейсы для ботов: отсутствует директория {current_path}')
            app_loger.critical(
                f'Невозможно получить интерфейсы для ботов: отсутствует директория {current_path}')
            app_loger.info(f'Создание интерфейсов прервано.')
            return interfaces_lst
        # Пролистываем все папки
        for (ext_dirpath, ext_dirnames, ext_filenames) in os.walk(current_path):
            for dirname in ext_dirnames:
                for (dirpath, dirnames, filenames) in os.walk(f'{current_path}\\{dirname}'):
                    for filename in filenames:
                        try:
                            if filename.endswith('.py'):
                                pos = filename.find('.py')
                                name_file = filename[:pos]
                                try:
                                    command_module = importlib.import_module(f'{py_path}.{dirname}.{name_file}')
                                except Exception as ex:
                                    err_str = str(ex)
                                    if err_str.find('No module named') == -1:
                                        print(f'Ошибка подключения интерфейса <{name_file}>. {err_str}')
                                        app_loger.warning(f'Ошибка подключения интерфейса <{name_file}>. {err_str}')
                                    continue
                                members = inspect.getmembers(command_module)
                                for name, obj in members:
                                    if inspect.isclass(obj):
                                        if issubclass(obj, BotViewInterface) and obj is not BotViewInterface:
                                            interfaces_lst.append(obj)
                                            app_loger.info(f'Загружен интерфейс <{obj.name}>')
                                            print(f'Загружен интерфейс <{obj.name}>')
                        except Exception as ex:
                            print(f'Ошибка загрузки интерфейса из {name_file}: {ex}')
                            app_loger.error(f'Ошибка загрузки интерфейса из {name_file}: {ex}')
        return interfaces_lst
    except Exception as ex:
        print(f'Ошибка загрузки интерфейсов: {ex}')
        app_loger.error(f'Ошибка загрузки интерфейсов: {ex}')
        return []

bot_interfaces = load_bot_interfaces()
pass

def get_bot_interface(name: str):
    for el in bot_interfaces:
        if el.name == name:
            return el
    return None

