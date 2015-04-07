from celery import shared_task
from gimmick.integration.facebook import client
from targetshare.models import SociallyEngagedUser
import datetime
from targetshare.integration.facebook import utils
import logging

@shared_task
def post_score(token):
    logging.info("in post score")
    post_stream = client.PostStream.read(token.fbid, token.token)
    post_score = post_stream.score()

    return post_score, post_stream

@shared_task
def like_score(token):
    like_stream = client.LikeStream.read(token.fbid, token.token)
    like_score = like_stream.score()

    return like_score, like_stream

@shared_task
def misc_info(token):
    logging.info("in misc info")
    user = client.get_user(token.token)
    logging.info(user)
    friends = client.get_friends(token.token)
    logging.info(friends)

    return user, friends, token.fbid

@shared_task
def compute_rankings(scoring_info):
    post_score, post_stream = scoring_info[0]
    like_score, like_stream = scoring_info[1]
    user, friends, fbid = scoring_info[2]

    score = like_score + post_score
    user_record = SociallyEngagedUser(
        fbid=user.fbid,
        first_name=user.fname,
        last_name=user.lname,
        birthday=utils.decode_date(user.birthday),
        city=user.city,
        state=user.state,
        gender=user.gender,
        score=score,
        updated=datetime.datetime.today(),
    )
    user_record.save()
    ranking_data = {
        'greenest_posts': post_stream[:3],
        'suggested_pages': [
            (8492293163, 'Environmental Defense Fund', 'https://www.facebook.com/EnvDefenseFund'),
            (15687409793, 'World Wildlife Fund', 'https://www.facebook.com/worldwildlifefund'),
            (8057376739, 'The Nature Conservancy', 'https://www.facebook.com/thenatureconservancy'),
        ],
    }
    friends_data = {}
    friends_data['top'] = []
    # friends rank
    friends_using_app = SociallyEngagedUser.objects.filter(
        fbid__in=[friend['id'] for friend in friends],
    ).order_by('score')
    for i, friend in enumerate(friends_using_app):
        if friend.fbid == fbid:
            friends_data['rank'] = i+1
        if i < 5:
            friends_data['top'].append((i+1, friend.fbid, friend.first_name, friend.last_name))

    ranking_data['friends'] = friends_data

    # city rank
    city_queryset = SociallyEngagedUser.objects.filter(city=user.city, state=user.state)
    ranking_data['city'] = {
        'user_city': user.city,
        'user_state': user.state,
        'rank': city_queryset.filter(score__gt=score).count() + 1,
        'total': city_queryset.count()
    }

    # age_rank
    born = utils.decode_date(user.birthday)
    now = datetime.datetime.today()
    age = now.year - born.year - ((now.month, now.day) < (born.month, born.day))
    start_date = datetime.date(now.year - age -1, now.month, now.day)
    end_date = datetime.date(now.year - age, now.month, now.day)
    age_queryset = SociallyEngagedUser.objects.filter(
        birthday__gt=start_date,
        birthday__lte=end_date,
    )
    ranking_data['age'] = {
        'user_age': age,
        'rank': age_queryset.filter(score__gt=score).count() + 1,
        'total': age_queryset.count()
    }

    return ranking_data
