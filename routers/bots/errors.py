import enum

class BotErrors(enum.Enum):
    NoError = 'ошибок нет, не запущен'
    MainBotCreateError = 'ошибка создания бота'
    InWork = 'работает'
    Stopped = 'остановлен'
    Broken = 'сломался'