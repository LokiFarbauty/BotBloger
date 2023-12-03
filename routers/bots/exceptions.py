from aiogram_dialog import DialogManager, StartMode

# async def on_unknown_intent(event, dialog_manager: DialogManager):
#     """Example of handling UnknownIntent Error and starting new dialog."""
#     #logger.error(f'Сработало исключение: неизвестный замысел: {event.exception}!')
#     #await dialog_manager.start(DialogSG.greeting, mode=StartMode.RESET_STACK, show_mode=ShowMode.SEND,)
#     pass


async def on_unknown_state(event, dialog_manager: DialogManager):
    """Example of handling UnknownState Error and starting new dialog."""
    #logging.error("Restarting dialog: %s", event.exception)
    #logger.error(f'Сработало исключение: неизвестное состояние: {event.exception}!')
    #print('Error: on_unknown_state')
    #await dialog_manager.start(DialogSG.greeting, mode=StartMode.RESET_STACK, show_mode=ShowMode.SEND,)
    pass

async def on_outdated_intent(event, dialog_manager: DialogManager):
    """Example of handling UnknownState Error and starting new dialog."""
    try:
        #await dialog_manager.done()
        await dialog_manager.reset_stack()
        #logger.error(f'Сработало исключение: on_outdated_intent: {event.exception}!')
    except:
        pass
    #await dialog_manager.start(states.SG_start_menu.start, mode=StartMode.RESET_STACK)