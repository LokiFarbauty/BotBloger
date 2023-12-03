'''Модуль нужен общему терминалу для обозначения комманд'''

import enum

class TerminalErrors(enum.Enum):
    NoError = 0
    PoorlyArgs = 'Недостаточно обязательных параметров'
    CommandNotFound = 'Команда неизвестна'

class Command():
    def __init__(self, name: str, func, args_num: int, help: str):
        self.func = func
        self.name = name
        self.args_num = args_num
        self.help = help

    def exec(self, args):
        try:
            ln = len(*args)
        except:
            ln = 0
        if ln>=self.args_num:
            return self.func(*args)
        else:
            return TerminalErrors.PoorlyArgs

# Собираем команды
class Commands():
    def __init__(self, *commands: Command):
        self.funcs = list(commands)

    def extend_funcs(self, *commands: Command):
        self.funcs.extend(commands)

    def command_exist(self, name: str):
        res = False
        for com in self.funcs:
            if com.name == name:
                return True
        return res

    def get_command(self, name: str):
        res = None
        for com in self.funcs:
            if com.name == name:
                return com
        return res

    def help(self):
        res = 'Формат команд: команда: параметр1, параметр2, ...\nДоступные команды:\n'
        for com in self.funcs:
            res = f'{res}{com.name} - {com.help}\n'
        return res

    def exec(self, name, *args):
        if self.command_exist(name):
            com = self.get_command(name)
            res = com.exec(*args)
            return res
        else:
            return TerminalErrors.CommandNotFound




