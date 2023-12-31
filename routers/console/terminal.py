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
            await asyncio.sleep(1)
            if first:
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
                args = []
                command = inp[:n]
                command = command.lower()
                pars = inp[n + 2:]
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
            # elif command=='create_test_bot':
            #     try:
            #         user = scripts.get_test_user()
            #         scripts.create_test_bot(user)
            #         print('Тестовый бот успешно создан')
            #     except Exception as ex:
            #         print(ex)
            # elif command=='vk_get_group_info':
            #     # Команда возвращает информацию о группе по id
            #     if len(args) > 0:
            #         res=parser_obj.get_vk_group_info(args[0])
            #         print(res)
            #     else:
            #         print(f'Ошибка: {err_no_parametrs}')
            #     pass
            # elif command=='vk_get_user_info':
            #     # Команда возвращает информацию о пользователе по id
            #     if len(args) > 0:
            #         res=parser_obj.get_vk_user_info(args[0])
            #         print(res)
            #     else:
            #         print(f'Ошибка: {err_no_parametrs}')
            #     pass
            # else:
            #
            #     print('Неправильная команда')
        except (KeyboardInterrupt, SystemExit):
            break
