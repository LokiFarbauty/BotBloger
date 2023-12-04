'''Команды для терминала, он заберает их отсюда'''

from routers.console.terminal_interface import Command
import routers.bots.telegram.bots as bots_unit

commands = []


# commands.append(
#     Command()
# )

async def get_bots_status():
     bot_info = ''
     for bot in bots_unit.current_bots:
          bot_info = f'{bot_info}{bot.name}({bot.tg_id}) - {bot.status.value}\n'
     return bot_info[:len(bot_info)-1]

commands.append(
     Command(name='get_bots_status', func=get_bots_status, args_num=0, help='Выводит статусы имеющихся ботов. Параметров нет.')
)

async def stop_bot(bot_tg_id):
     for bot in bots_unit.current_bots:
          try:
               if bot.tg_id == int(bot_tg_id):
                    was_cancelled = await bot.stop_polling()
                    return was_cancelled
          except Exception as ex:
               return ex
     return 'бот не найден'

commands.append(
     Command(name='stop_bot', func=stop_bot, args_num=1, help='Остановить работающего бота. Параметр 1: id бота.')
)

async def start_bot(bot_tg_id):
     for bot in bots_unit.current_bots:
          try:
               if bot.tg_id == int(bot_tg_id):
                    await bot.start_polling_task()
          except Exception as ex:
               return ex

commands.append(
     Command(name='start_bot', func=start_bot, args_num=1, help='Запустить бота. Параметр 1: id бота.')
)