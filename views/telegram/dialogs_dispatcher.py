import os
import importlib
import inspect
from aiogram_dialog import Dialog

from main_config import MAIN_PATH

from routers.logers import app_loger

#dlg_path = MAIN_PATH
dlg_path = os.path.dirname(os.path.abspath(__file__))+'\\dialogs\\' # путь к файлам диалогов
py_dlg_path = 'views.telegram.dialogs'

def get_dialogs(path=dlg_path, py_path=py_dlg_path):
    dialogs_lst = []
    # проверяем директорию
    if not os.path.isdir(path):
        app_loger.critical(
            f'Невозможно получить диалоги для ботов: отсутствует директория {path}')
        app_loger.info(f'Создание диалогов прервано.')
        return dialogs_lst
    # Получаем список файлов в папке диалогов
    dialog_files = os.listdir(path)
    # Пробуем подключить парсеры
    cur_dlg_clases = []
    for dlg_file in dialog_files:
        try:
            pos = dlg_file.find('.py')
            if pos == -1:
                continue
            else:
                dlg_file = dlg_file[:pos]
            #
            command_module = importlib.import_module(f'{py_path}.{dlg_file}')
            vars_objs = vars(command_module).items()
            for name, values in vars_objs:
                if type(values) is Dialog:
                    if values not in cur_dlg_clases:
                        cur_dlg_clases.append(values)
            # Добавляем диалоги
            for att_dlg in cur_dlg_clases:
                if att_dlg not in dialogs_lst:
                    dialogs_lst.append(att_dlg)
        except Exception as ex:
            app_loger.error(f'Ошибка загрузки диалога {dlg_file}: {ex}')
    return dialogs_lst

bot_dialogs = get_dialogs()