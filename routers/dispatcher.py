'''Этот модуль содержит глобальные объекты - роутеры'''

from routers.parsing.parsing_dispatсher import ParserDispatcher
from routers.logers import app_loger

parsing_dispatcher = ParserDispatcher(app_loger)