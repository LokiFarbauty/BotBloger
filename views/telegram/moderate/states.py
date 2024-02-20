from aiogram.fsm.state import State, StatesGroup


class SG_Main(StatesGroup):
    start = State()
    programm = State()
    for_viewing = State()
    scheme = State()
    ads = State()

# class SG_enter_token_menu(StatesGroup):
#     make_vk_sync = State()
#     make_bot = State()
#     get_channel = State()
#     get_vk_token = State()
#     token_got = State()
#     create_assign_vk = State()
#     get_user_id = State()
#     make_vk_sync_final = State()
#     vk_sync_maked = State()
#     where_token = State()
#     why_token = State()
#     why_bot = State()

