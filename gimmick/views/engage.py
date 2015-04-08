import datetime
import re

import celery
from django import http
from django.core.urlresolvers import reverse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods

from core.utils import oauth, signed
from core.utils.version import make_version
from core.utils.http import JsonHttpResponse
from core.utils.sharingurls import fb_oauth_url
from targetshare.models.relational import FBApp
from targetshare.tasks.integration.facebook import store_oauth_token

from gimmick import tasks
from gimmick.models import EngagedUser


API_VERSION = make_version('2.3')

DEFAULT_APPID = 555738104565910

EMBEDDED_NS_PATTERN = re.compile(r'\bcanvas\b')
EMBEDDED_PATH_TOKEN = '/canvas/'


def get_embedded_path(fb_app, path):
    (_base_path, rel_path) = path.rsplit(EMBEDDED_PATH_TOKEN, 1)
    return 'https://apps.facebook.com/{}/{}'.format(fb_app.name, rel_path)


fb_signed = signed.fb_signed.configured(default_appid=DEFAULT_APPID)


@fb_signed
@csrf_exempt
@require_http_methods(['GET', 'POST'])
def intro(request, appid, signed):
    fb_app = FBApp.objects.get(appid=appid)
    namespace = request.resolver_match.namespace

    if namespace and EMBEDDED_NS_PATTERN.search(namespace):
        # Request received from Facebook canvas --
        # main app should be served from canvas as well.

        # Remove the true path base from FB vanity URL path:
        true_path = reverse('gimmick-canvas:engage')
        redirect_uri = get_embedded_path(fb_app, true_path)
    else:
        # Unembedded.
        redirect_path = reverse('gimmick:engage')
        redirect_uri = request.build_absolute_uri(redirect_path)

    return render(request, 'gimmick/intro.html', {
        # TODO: initial redirector?
        'initial_url': fb_oauth_url(fb_app, redirect_uri),
    })


@fb_signed
@csrf_exempt
@require_http_methods(['GET', 'POST'])
def main(request, appid, signed):
    try:
        signature = oauth.handle_incoming(request)
    except oauth.AccessDenied:
        signature = oauth.AccessSignature()

    if not signature.is_valid():
        # OAuth circumvented or denied
        # Record auth fail and redirect to error URL:
        # TODO: event
        namespace = request.resolver_match.namespace or 'gimmick'
        path = reverse(namespace + ':engage-intro') + "#denied"
        if EMBEDDED_NS_PATTERN.search(namespace):
            fb_app = FBApp.objects.get(appid=appid)
            url = get_embedded_path(fb_app, path)
            return render(request, 'chapo/redirect.html', {'url': url})
        else:
            return redirect(path)

    session_key = 'engage_task_{}'.format(signature.code)
    try:
        task_id = request.session[session_key]
    except KeyError:
        chain = (
            store_oauth_token.s(
                signature.code,
                signature.redirect_uri,
                api=API_VERSION,
                app_id=appid,
            ) |
            celery.group(tasks.score_posts.s(), tasks.score_likes.s(), tasks.read_network.s())
        )
        task = chain.apply_async()
        task_id = request.session[session_key] = task.id

    return render(request, 'gimmick/engage.html', {
        'task_id': task_id,
    })


@require_GET
def data(request, task_id):
    task = celery.current_app.AsyncResult(task_id)

    if not task.ready():
        return JsonHttpResponse({'status': 'waiting'}, status=202)

    # Check result #
    result = task.result if task.successful() else None
    if not result:
        return http.HttpResponseServerError()

    # TODO: events?
    return JsonHttpResponse({
        'status': 'success',
        'results': compute_rankings(*result),
    })


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


def compute_rankings(scored_posts, scored_likes, user_network):
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
                'fbid': friend.fbid,
                'first_name': 'You',
                'last_name': '',
            })
        elif rank <= 5:
            data['friends']['top'].append({
                'rank': rank,
                'fbid': friend.fbid,
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
