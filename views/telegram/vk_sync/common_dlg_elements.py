
from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Cancel, Button, Back, Select, SwitchTo, Start
from aiogram_dialog.widgets.text import Const, Format, Multi
#

async def event_back_window(callback: CallbackQuery, button: Button,
                    dialog_manager: DialogManager):
    '''Событие нажатия на кнопку - Назад (возврат в предидущее окно)'''
    await dialog_manager.back()

# Возвращает в предидущий диалог
BTN_BACK_WINDOW=Button(
    text=Const('🔙 Назад'),
    id='btn_back_window',
    on_click=event_back_window)