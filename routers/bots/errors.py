'''В модуле определены ошибки, которые могут возникать в работе ботов'''

import enum

class BotErrors(enum.Enum):
    NoError = 'ошибок нет, не запущен'
    MainBotCreateError = 'ошибка создания бота'
    InWork = 'работает'
    Stopped = 'остановлен'
    Broken = 'сломался'