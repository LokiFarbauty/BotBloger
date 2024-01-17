from abc import ABC, abstractmethod

class BotViewInterface(ABC):
    name = 'None'
    description = 'Этот интерфейс шаблон любого интерфейса бота.'
    dialogs = [] # Диалоги

    @classmethod
    @abstractmethod
    async def start(cls):
        return None