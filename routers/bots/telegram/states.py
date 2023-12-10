from aiogram.fsm.state import State, StatesGroup


class SG_start_menu(StatesGroup):
    start = State()

class SG_enter_token_menu(StatesGroup):
    start = State()
    where_token = State()
    why_token = State()
    token_got = State()
    get_user_id = State()

class SG_nothing(StatesGroup):
    start = State()

class SG_find_post(StatesGroup):
    input_words = State()
    show_result = State()

class SG_favourites(StatesGroup):
    start = State()

class SG_tops(StatesGroup):
    start = State()

class SG_news(StatesGroup):
    start = State()

class SG_random(StatesGroup):
    start = State()

class SG_topic(StatesGroup):
    choose_topics = State()
    view_post = State()

class SG_offer_post(StatesGroup):
    add_text = State()
    add_img = State()
    finish = State()


