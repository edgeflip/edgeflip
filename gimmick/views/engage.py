import re

import celery
from django import http
from django.core.urlresolvers import reverse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods

from core.utils import oauth, signed
from core.utils.version import make_version
from core.utils.http import JsonHttpResponse
from core.utils.sharingurls import fb_oauth_url
from targetshare.models.relational import FBApp
from targetshare.tasks.integration.facebook import store_oauth_token

from gimmick import tasks


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
            celery.group(tasks.score_posts.s(), tasks.score_likes.s(), tasks.read_network.s()) |
            tasks.compute_rankings.s() # celery won't give us a collected group ID,
                                       # so post-process in a chord callback
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
    results = task.result if task.successful() else None
    if not results:
        return http.HttpResponseServerError()

    # TODO: events?
    return JsonHttpResponse({
        'status': 'success',
        'results': results,
    })
