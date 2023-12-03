'''Это модуль данных
Для добавления моделей просто создайте файл с моделью в папке data.
Модуль сам создаст соответствующую таблицу в базе'''

from peewee import Model
from playhouse.sqlite_ext import FTS5Model, FTSModel
from os import listdir
from os.path import isfile, join
import enum
import importlib
import inspect
#
import models.dm_config as dm_config

class Errors(enum.Enum):
    NoError = 0
    PyError = -1
    ImportPyModuleError = 1


def get_elements(model, condition=None):
    # Получаем элементы из базы
    if condition!=None:
        elements = model.select().where(condition)
    else:
        elements = model.select()
    return elements


def create_data_model():
    # Получаем список файлов в папке c моделям
    onlyfiles = [f for f in listdir(dm_config.DBM_DATA_PATH) if isfile(join(dm_config.DBM_DATA_PATH, f))]
    # Ищем в каждом файле наследников класа
    for file in onlyfiles:
        try:
            # Проверяем что это файл скрипта
            pos = file.find('.py')
            if pos == -1:
                continue
            else:
                file = file[:pos]
            # Пытаемся загрузить файл
            command_module = importlib.import_module(f'{dm_config.DBM_MODELS_DIR}.{dm_config.DBM_DATA_DIR}.{file}')
        except Exception as ex:
            continue
            #return Errors.ImportPyModuleError
        # Проверяем модуль на предмет наличия там класса Model
        cur_dm = None
        tables = []  # Найденые модели
        try:
            # Ищем модели и добавляем их в список tables
            members = inspect.getmembers(command_module)
            for name, obj in members:
                if inspect.isclass(obj):
                    subclass = issubclass(obj, (Model, FTS5Model, FTSModel))
                    if subclass and obj is not Model and obj is not FTS5Model and obj is not FTSModel:
                        tables.append(obj)
        finally:
            try:
                dm_config.db.create_tables(tables)
            except Exception as ex:
                print(f'Ошибка создания модели данных. Причина {ex}')




if not isfile(dm_config.DB_FILE_PATH):
    try:
        create_data_model()
    except Exception as ex:
        print(f'Создать базу данных не удалось. Причина: {ex}')
else:
    create_data_model()


