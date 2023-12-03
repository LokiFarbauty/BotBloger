from aiogram_dialog import DialogManager

def get_offset(dialog_manager: DialogManager, data_key: str):
    data = dialog_manager.dialog_data
    try:
        offset = data['offset']
    except:
        offset = 0
        data['offset'] = 0
    # Защищаем выход индекса за границу
    if offset >= len(data[f'{data_key}']): offset = 0
    if offset < 0: offset = len(data[f'{data_key}']) - 1
    data['offset'] = offset
    return offset

def get_offset_ex(dialog_manager: DialogManager, data_key: str):
    data = dialog_manager.dialog_data
    try:
        offset = data[f'{data_key}_offset']
    except:
        offset = 0
        data[f'{data_key}_offset'] = 0
    # Защищаем выход индекса за границу
    if offset >= len(data[f'{data_key}']): offset = 0
    if offset < 0: offset = len(data[f'{data_key}']) - 1
    data[f'{data_key}_offset']=offset
    return offset

def get_current_dialog_data(dialog_manager: DialogManager, data_key: str):
    #data = dialog_manager.start_data
    data = dialog_manager.dialog_data
    try:
        offset = data['offset']
    except:
        offset = 0
        data['offset'] = 0
    # Защищаем выход индекса за границу
    if offset >= len(data[f'{data_key}']): offset = 0
    if offset < 0: offset = len(data[f'{data_key}']) - 1
    dialog_manager.dialog_data['offset'] = offset
    # Выбираем элемент
    try:
        res=data[f'{data_key}'][offset]
    except:
        res=[]
    return res