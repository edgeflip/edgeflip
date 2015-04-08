from celery import shared_task
from celery.utils.log import get_task_logger

from gimmick.integration.facebook import client


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
