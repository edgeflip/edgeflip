import datetime

from celery import shared_task
from celery.utils.log import get_task_logger
from django.utils import timezone

from gimmick.integration.facebook import client
from gimmick.models import EngagedUser


LOG = get_task_logger(__name__)


@shared_task
def score_posts(token):
    post_stream = client.EnvironmentPostStream.read(token.fbid, token.token)
    post_score = post_stream.score()
    return (post_score, post_stream)


@shared_task
def score_likes(token):
    like_stream = client.EnvironmentLikeStream.read(token.fbid, token.token)
    like_score = like_stream.score()
    return (like_score, like_stream)


@shared_task
def read_network(token):
    user = client.get_user(token.token)
    friends = client.get_friends(token.token)
    return (user, friends)


def update_or_create_user(fbid, data):
    (engaged_user, created) = EngagedUser.objects.get_or_create(fbid=fbid, defaults=data)

    if not created:
        for (key, value) in data.iteritems():
            setattr(engaged_user, key, value)
        engaged_user.save()

    return engaged_user


def make_date(year, month, day):
    try:
        return datetime.date(year, month, day)
    except ValueError:
        # Feb 29
        return datetime.date(year, month, day - 1)


@shared_task
def compute_rankings(results):
    (scored_posts, scored_likes, user_network) = results
    (post_score, post_stream) = scored_posts
    (like_score, like_stream) = scored_likes
    (user, friends) = user_network

    engaged_user = update_or_create_user(user.fbid, {
        'first_name': user.fname,
        'last_name': user.lname,
        'birthday': user.birthday,
        'city': user.city,
        'state': user.state,
        'gender': user.gender,
        'score': like_score + post_score,
    })

    data = {
        'greenest_posts': [
            {
                'message': post.message,
                'post_id': post.post_id,
                'score': post.score,
            } for post in post_stream[:3]
        ],
        'greenest_likes': [
            {
                'name': like.name,
                'page_id': like.page_id,
            } for like in like_stream[:3]
        ],
        'suggested_pages': [
            (8492293163, 'Environmental Defense Fund', 'https://www.facebook.com/EnvDefenseFund'),
            (15687409793, 'World Wildlife Fund', 'https://www.facebook.com/worldwildlifefund'),
            (8057376739, 'The Nature Conservancy', 'https://www.facebook.com/thenatureconservancy'),
        ],
        'city': {
            'user_city': user.city,
            'user_state': user.state,
            'rank': EngagedUser.objects.filter(city=user.city, state=user.state).filter(
                score__gt=engaged_user.score
            ).count() + 1,
        },
        'friends': {'rank': 1, 'top': []},
    }

    # Fill in friends rank
    all_fbids = [friend.fbid for friend in friends] + [user.fbid]
    friends_using_app = EngagedUser.objects.filter(fbid__in=all_fbids)
    for (rank, friend) in enumerate(friends_using_app.order_by('-score').iterator(), 1):
        if friend.fbid == user.fbid:
            data['friends']['rank'] = rank
            data['friends']['top'].append({
                'rank': rank,
                'fbid': str(friend.fbid),
                'first_name': 'You',
                'last_name': '',
            })
        elif rank <= 5:
            data['friends']['top'].append({
                'rank': rank,
                'fbid': str(friend.fbid),
                'first_name': friend.first_name,
                'last_name': friend.last_name,
            })

    # Add age rank
    user_age = user.age
    today = timezone.now().date()
    start_date = make_date(today.year - user_age - 1, today.month, today.day)
    end_date = make_date(today.year - user_age, today.month, today.day)
    user_peers = EngagedUser.objects.filter(birthday__gt=start_date, birthday__lte=end_date)
    data['age'] = {
        'user_age': user_age,
        'rank': user_peers.filter(score__gt=engaged_user.score).count() + 1,
    }

    return data
