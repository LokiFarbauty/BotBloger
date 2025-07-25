from abc import ABC, abstractmethod
from aiogram.fsm.state import State, StatesGroup

class BotViewInterface(ABC):
    name = 'None'
    description = 'Этот интерфейс шаблон любого интерфейса бота.'
    file = ''
    dialogs = [] # Диалоги
    start_dialog: StatesGroup = None
    #start_state: State = None # !!! в определенном диалоге всегда первым будет запускаться State - start оно должно быть обязательно

    # @classmethod
    # @abstractmethod
    # async def start(cls):
    #     return None