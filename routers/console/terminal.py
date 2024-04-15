'''Головной модуль терминала'''

import datetime
import os
from aioconsole import ainput
import asyncio

# routers

# models

#
from routers.console.terminal_interface import Commands, TerminalErrors
from models.terminal_commands import commands as model_commands
from routers.terminal_commands import commands as parsing_commands
from routers.bots.terminal_commands import commands as bot_commands


err_no_parametrs='не указаны требуемые параметры'

async def console(args):
    first = True
    while True:
        try:
            await asyncio.sleep(0.1)
            if first:
                await asyncio.sleep(5)
                print('Терминал активен, можно вводить команды:')
                try:
                    # Создаем коммандный интерфейс
                    commands = Commands()
                    commands.extend_funcs(*model_commands)
                    commands.extend_funcs(*parsing_commands)
                    commands.extend_funcs(*bot_commands)
                    pass
                except Exception as ex:
                    print(f'Ошибка загрузки терминала: {ex}')
                first = False
            inp = await ainput('>>> ')
            dt_now = datetime.datetime.now()
            dt_now = dt_now.replace(microsecond=0)
            dt_now = dt_now.timestamp()
            n = inp.find(': ')
            pars = ''
            if n == -1:
                command = inp
                args=[]
            else:
                # Есть параметры
                #  Проверяем на кавычки
                args = []
                command = inp[:n]
                command = command.lower()
                pars = inp[n + 2:]
                for j in range(1,1000):
                    q_pos_s = pars.find("'")
                    q_pos_e = pars.find("'", q_pos_s+1)
                    if q_pos_s == -1 or q_pos_e == -1:
                        break
                    else:
                        par1 = pars[q_pos_s+1:q_pos_e]
                        par1_0 = f"'{par1}',"
                        par1_1 = f"'{par1}'"
                        pars = pars.replace(par1_0, '')
                        pars = pars.replace(par1_1, '')
                    args.append(par1.strip())
                #
                if pars != '':
                    args0=pars.split(',')
                    for el in args0:
                        try:
                            int_el = int(el)
                            args.append(int_el)
                        except:
                            args.append(el.strip())
            command = command.strip()
            if command=='exit':
                os._exit(0)
            elif command=='test':
                pass
            elif command=='help' or command == '?':
                try:
                    help=commands.help()
                    print(help)
                except Exception as ex:
                    print(ex)
            else:
                if commands.command_exist(command):
                    try:
                        res = await commands.exec(command, args)
                        if type(res) is not TerminalErrors:
                            try:
                                if type(res) is str:
                                    raise
                                object_iterator = iter(res)
                                for el in res:
                                    print(el)
                            except:
                                print(res)
                        else:
                            print(f'Ошибка: {res.value}')
                    except Exception as ex:
                        print(ex)
                else:
                    print('Неизвестная команда')
        except (KeyboardInterrupt, SystemExit):
            break
