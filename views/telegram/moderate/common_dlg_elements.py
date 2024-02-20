
from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager, StartMode
from aiogram_dialog.widgets.kbd import Cancel, Button, Back, Select, SwitchTo, Start
from aiogram_dialog.widgets.text import Const, Format, Multi
#
from views.telegram.moderate import states
#
from models.data.user import User
from models.data.post import Post, ModerateStates
from models.data.video import Video
from models.data.audio import Audio
from models.data.poll import Poll
from models.data.link import Link
from models.data.docs import Doc
#
from datetime import datetime
from dataclasses import dataclass

@dataclass
class PostDesc:
    POST_TEXT: str = ''
    POST_DESC: str = ''
    POST_EXIST: bool = False

async def get_post_desc(post: Post, post_text: str, offset: int, user: User, posts_count = 0, debug=False) -> PostDesc:
    # Получаем видео
    videos = Video.select().where(Video.owner == post)
    for video in videos:
        post_text = f'{post_text}\n🎞 {video.title}\n{video.url}'
    # Получаем ссылки
    links = Link.select().where(Link.owner == post)
    for link in links:
        post_text = f'{post_text}\n🔗 {link.title}\n{link.url}'
    # Получаем опросы
    polls = Poll.select().where(Poll.owner == post)
    first = True
    for poll in polls:
        if first:
            post_text = f'{post_text}\n'
            first = not first
        answers = poll.answers.split('|| ')
        answers_str = ''
        for i, answer in enumerate(answers, 1):
            answers_str = f'{answers_str}🔘 {answer}\n'
        post_text = f'{post_text}\n{poll.question}\n{answers_str}'
    # Получаем аудио
    audios = Audio.select().where(Audio.owner == post)
    first = True
    for audio in audios:
        if first:
            post_text = f'{post_text}\n'
            first = not first
        post_text = f'{post_text}\n🎵{audio.artist}-{audio.title}'
    # Получаем ссылки
    docs = Doc.select().where(Doc.owner == post)
    for doc in docs:
        post_text = f'{post_text}\n📁 {doc.url}'
    #
    dt = post.dt
    dt = datetime.fromtimestamp(dt).strftime('%d.%m.%Y')
    program_name = post.parse_program.name
    task_name = post.parse_task.name
    if debug:
        post_id = post.get_id()
        post_desc = f'Программа: <b>"{program_name}"</b>. Источник: <b>"{task_name}"</b>. id: <b>{post_id}</b>. Опубликовано: <b>{dt}</b>. Просмотров: <b>{post.old_views}</b>. Лайков: <b>{post.likes}</b>. {offset+1} из <b>{posts_count}</b>.\n'
    else:
        post_desc = f'Программа: <b>{program_name}</b>. Источник: <b>{task_name}</b>. Опубликовано: <b>{dt}</b>. Просмотров: <b>{post.old_views}</b>. Лайков: <b>{post.likes}</b>. {offset+1} из <b>{posts_count}</b>.\n'
    post_exist = True
    res = PostDesc(POST_TEXT=post_text, POST_DESC=post_desc, POST_EXIST=post_exist)
    return res

async def event_next_case(callback: CallbackQuery, button: Button,
                    dialog_manager: DialogManager):
    data = dialog_manager.dialog_data
    try:
        offset = data['offset']
    except:
        offset = 0
    offset+=1
    dialog_manager.dialog_data['offset']=offset
    #
    try:
        aiogd_context = data['aiogd_context']
        aiogd_context.widget_data['text_scroll_post'] = 0
    except:
        pass

NEXT_CASE_BUTTON = Button(
    Const('➡️'),
    on_click=event_next_case,
    id="btn_next_case"
)

async def event_prev_case(callback: CallbackQuery, button: Button,
                    dialog_manager: DialogManager):
    data = dialog_manager.dialog_data
    try:
        offset = data['offset']
    except:
        offset = 0
    offset-=1
    if offset<0:
        offset=0
    dialog_manager.dialog_data['offset']=offset
    try:
        aiogd_context = data['aiogd_context']
        aiogd_context.widget_data['text_scroll_post'] = 0
    except:
        pass

PREV_CASE_BUTTON = Button(
    Const('⬅️'),
    on_click=event_prev_case,
    id="btn_prev_case"
)

async def event_del_post(callback: CallbackQuery, button: Button,
                    dialog_manager: DialogManager):
    post = dialog_manager.dialog_data['post']
    post.moderate = ModerateStates.ToDelete.value
    post.save()
    pass

DEL_POST_BUTTON = Button(
    Const('🗑'),
    on_click=event_del_post,
    id="btn_del_post"
)

async def event_skip_post(callback: CallbackQuery, button: Button,
                    dialog_manager: DialogManager):
    post = dialog_manager.dialog_data['post']
    post.moderate = ModerateStates.InArchive.value
    post.save()
    pass

SKIP_POST_BUTTON = Button(
    Const('📥'),
    on_click=event_skip_post,
    id="btn_skip_post"
)

async def event_public_post(callback: CallbackQuery, button: Button,
                    dialog_manager: DialogManager):
    post = dialog_manager.dialog_data['post']
    post.moderate = ModerateStates.ToPublish.value
    post.save()
    pass

PUBLIC_POST_BUTTON = Button(
    Const('📇'),
    on_click=event_public_post,
    id="btn_public_post"
)

async def show_main_menu(callback: CallbackQuery = None, dialog_manager: DialogManager = None):
    await dialog_manager.start(states.SG_Main.start, mode=StartMode.RESET_STACK)


async def event_back(callback: CallbackQuery, button: Button,
                    dialog_manager: DialogManager):
    '''Событие нажатия на кнопку - Назад'''
    try:
        stack = dialog_manager.current_stack()
        stack_len=len(stack.intents)
        #await dialog_manager.done()
        if stack_len<=1:
            await show_main_menu(callback, dialog_manager)
        else:
            await dialog_manager.back()
    except Exception as ex:
        #print(ex)
        pass

# Возвращает в предидущий диалог
BTN_BACK=Button(
    text=Const('⏏️'),
    id='btn_back',
    on_click=event_back)
