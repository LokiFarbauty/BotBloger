
from models.data.parse_task import ParseTask
from models.data.post import Post
from peewee import fn
from routers.logers import parsers_loger

async def refresh_avg_rating(parse_task: ParseTask):
    avg_views = Post.select(fn.AVG(Post.old_views)).where(Post.parse_task==parse_task).scalar()
    avg_likes = Post.select(fn.AVG(Post.likes)).where(Post.parse_task==parse_task).scalar()
    try:
        avg_rate = avg_likes / avg_views
    except:
        avg_rate = 0
    parse_task.avg_post_rate = avg_rate
    parse_task.save()

async def get_avg_views(parse_task: ParseTask) -> int:
    try:
        avg_views = Post.select(fn.AVG(Post.old_views)).where(Post.parse_task==parse_task).scalar()
    except:
        avg_views = 0
    return avg_views

async def refresh_max_rating(parse_task: ParseTask):
    try:
        max_base_rate = 0
        max_likes_posts = Post.select().where((parse_task == parse_task))
        for max_likes_post in max_likes_posts:
            max_likes = max_likes_post.likes
            max_views = max_likes_post.old_views
            if max_likes>0 and max_views>0:
                max_base_rate_tmp = max_views / max_likes
                if max_base_rate < max_base_rate_tmp:
                    max_base_rate = max_base_rate_tmp
        parse_task.max_post_rate = max_base_rate
        parse_task.save()
        return max_base_rate
    except:
        # расчитать рейтинг не возможно нет базовых значений
        return 0

async def refresh_min_rating(parse_task: ParseTask):
    try:
        min_base_rate = 0
        min_likes_posts = Post.select().where((parse_task == parse_task))
        for min_likes_post in min_likes_posts:
            min_likes = min_likes_post.likes
            min_views = min_likes_post.old_views
            if min_likes>0 and min_views>0:
                min_base_rate_tmp = min_views / min_likes
                if min_base_rate > min_base_rate_tmp:
                    min_base_rate = min_base_rate_tmp
        parse_task.min_post_rate = min_base_rate
        parse_task.save()
        return min_base_rate
    except:
        # расчитать рейтинг не возможно нет базовых значений
        return 0

async def refresh_posts_rating(parse_task: ParseTask, method = 1):
    # Получаем максимум просмотров
    # max_views = Post.select(fn.MAX(Post.old_views)).scalar()
    # Получаем максимум лайков
    parsers_loger.info(f'Начат расчет рейтингов для задачи "{parse_task.name}" ...')
    if method == 0:
        max_base_rate = parse_task.max_post_rate
        if max_base_rate == 0 or max_base_rate == None:
            max_base_rate = await refresh_max_rating(parse_task)
        # Просматриваем все посты и рассчитываем рейтинг
        if max_base_rate > 0:
            posts = Post.select().where(Post.parse_task == parse_task)
            for post in posts:
                rate = 0
                try:
                    if post.likes != 0:
                        base_rate = post.old_views / post.likes
                    else:
                        base_rate = 0
                except:
                    base_rate = 0
                if base_rate > 0 and base_rate <= max_base_rate / 10:
                    rate = 0.1
                if base_rate > max_base_rate / 10 and base_rate <= max_base_rate / 5:
                    rate = 0.2
                if base_rate > max_base_rate / 5 and base_rate <= max_base_rate / 2.5:
                    rate = 0.4
                if base_rate > max_base_rate / 2.5 and base_rate <= max_base_rate / 1.7:
                    rate = 0.6
                if base_rate > max_base_rate / 1.7 and base_rate <= max_base_rate / 1.3:
                    rate = 0.8
                if base_rate > max_base_rate / 1.3:
                    rate = 1
                if base_rate == 0:
                    rate = 0
                #
                post.rate = rate
                post.save()
        else:
            parsers_loger.info(f'Расчет рейтингов задачи "{parse_task.name}" невозможен.')
    if method == 1:
        posts = Post.select().where(Post.parse_task == parse_task)
        for post in posts:
            try:
                if post.old_views != 0:
                    rate = post.likes / post.old_views
                else:
                    rate = 0
            except:
                rate = 0
            #
            post.rate = rate
            post.save()
    parsers_loger.info(f'Расчет рейтингов для задачи "{parse_task.name}" закончен.')