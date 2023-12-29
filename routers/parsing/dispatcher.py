'''Этот модуль содержит глобальные объекты - диспетчер парсеров.
Он отвечает за автоматическую подгрузку парсеров из папки parsers.
Парсеры подгружаются при создании объекта ParserDispatcher и дальше хранятся в нем'''

from routers.parsing.parsing_dispatсher import ParserDispatcher
from routers.logers import parsers_loger

parsing_dispatcher = ParserDispatcher(parsers_loger)