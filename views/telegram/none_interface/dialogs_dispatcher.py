'''Модуль при импорте автоматически подгружает и привязывает к боту все диалоги изпапки dialogs'''

'''Модуль при импорте автоматически подгружает и привязывает к боту все диалоги изпапки dialogs'''

import os
import importlib
import inspect
from aiogram.fsm.state import State, StatesGroup
from aiogram_dialog import Dialog
#
from routers.logers import bots_loger
#
from views.telegram.interface_pattern import BotViewInterface
# Диалоги
from views.telegram.none_interface.dialogs.start_dialog import Dialog_state

#dlg_path = MAIN_PATH
dlg_path = os.path.dirname(os.path.abspath(__file__))+'\\dialogs\\' # путь к файлам диалогов
py_dlg_path = 'views.telegram.none_interface.dialogs'


def get_dialogs(path=dlg_path, py_path=py_dlg_path):
    # Подгружаем все найденые диалоги
    dialogs_lst = []
    # проверяем директорию
    if not os.path.isdir(path):
        bots_loger.critical(
            f'Невозможно получить диалоги для ботов: отсутствует директория {path}')
        bots_loger.info(f'Создание диалогов прервано.')
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
            bots_loger.error(f'Ошибка загрузки диалога {dlg_file}: {ex}')
    return dialogs_lst


class BotView(BotViewInterface):
    name = 'None'
    description = 'Базовый интерфейс бота'
    file = os.path.abspath(__file__)
    dialogs = get_dialogs()
    start_dialog_name = 'Dialog_state'
    start_state_name = f'{start_dialog_name}:start'
    start_dialog = Dialog_state
    #start_state = Dialog_state.start
    pass
    # Ищем стартовый диалог




