import celery
from django import http
from django.conf import settings
from django.core.urlresolvers import reverse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods

from core.utils import oauth, signed
from core.utils.version import make_version
from core.utils.http import JsonHttpResponse
from core.utils.sharingurls import fb_oauth_url
from targetshare.models.datastructs import ShortToken
from targetshare.models.relational import FBApp
from targetshare.tasks.integration.facebook import store_oauth_token

from gimmick import tasks


API_VERSION = make_version('2.3')

DEFAULT_APPID = 555738104565910


fb_signed = signed.fb_signed.configured(
    origin='', # Same-Origin check disabled for Firefox
    default_appid=DEFAULT_APPID,
)


@fb_signed
@csrf_exempt
@require_http_methods(['GET', 'POST'])
def intro(request, appid, signed):
    fb_app = FBApp.objects.get(appid=appid)
    namespace = request.resolver_match.namespace

    if namespace and oauth.EMBEDDED_NS_PATTERN.search(namespace):
        # Request received from Facebook canvas --
        # main app should be served from canvas as well.

        # Remove the true path base from FB vanity URL path:
        true_path = reverse('gimmick-canvas:engage')
        redirect_uri = oauth.get_embedded_path(fb_app, true_path)
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
    fb_app = FBApp.objects.get(appid=appid)

    try:
        signature = oauth.handle_incoming(request, fb_app)
    except oauth.AccessDenied:
        signature = oauth.AccessSignature()

    if not signature.is_valid():
        # OAuth circumvented or denied
        # Record auth fail and redirect to error URL:
        # TODO: event
        namespace = request.resolver_match.namespace or 'gimmick'
        path = reverse(namespace + ':engage-intro') + "#denied"
        if oauth.EMBEDDED_NS_PATTERN.search(namespace):
            url = oauth.get_embedded_path(fb_app, path)
            return render(request, 'chapo/redirect.html', {'url': url})
        else:
            return redirect(path)

    session_key = 'engage_task_{}'.format(signature.code)
    try:
        task_id = request.session[session_key]
    except KeyError:
        oauth_token_job = store_oauth_token.s(
            signature.code,
            signature.redirect_uri,
            api=API_VERSION,
            app_id=appid,
        )
        scoring_job = celery.group(tasks.score_posts.s(),
                                   tasks.score_likes.s(),
                                   tasks.read_network.s())

        if signed and 'oauth_token' in signed and 'user_id' in signed:
            oauth_token_job.apply_async()
            token = ShortToken(
                fbid=int(signed['user_id']),
                appid=appid,
                token=signed['oauth_token'],
                api=API_VERSION,
            )
            chain_start = scoring_job.clone((token,))
        else:
            chain_start = oauth_token_job | scoring_job

        # celery won't give us a collected group ID, so post-process in a chord callback
        chain = chain_start | tasks.compute_rankings.s()
        task = chain.apply_async()
        task_id = request.session[session_key] = task.id

    return render(request, 'gimmick/engage.html', {
        'fb_app': fb_app,
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


def fb_object(request, appid, rank):
    fb_app = FBApp.objects.get(appid=appid)

    namespace = request.resolver_match.namespace or 'gimmick'
    path = reverse(namespace + ':engage-intro')
    if oauth.EMBEDDED_NS_PATTERN.search(namespace):
        redirect_url = oauth.get_embedded_path(fb_app, path)
    else:
        redirect_url = 'https://{}{}'.format(request.get_host(), path)

    return render(request, 'gimmick/fb_object.html', {
        'fb_app': fb_app,
        'rank': rank,
        'fb_object_url': request.build_absolute_uri(),
        'fb_img_url': request.build_absolute_uri(settings.STATIC_URL + 'img/blue-logo.png'),
        'fb_obj_type': 'ranking',
        'redirect_url': redirect_url,
    })
