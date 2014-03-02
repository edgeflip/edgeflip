import collections
import functools

import celery
from django import http
from django import forms
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST

from targetshare.integration import facebook
# from targetshare.models import relational
from targetshare.tasks import db, ranking
from targetshare.views import utils


FB_APP_ID = 471727162864364

require_visit = functools.partial(utils.require_visit, appid=FB_APP_ID)


class DataForm(forms.Form):
    """Data request validation form."""
    fbid = forms.IntegerField(min_value=1)
    token = forms.CharField()


@require_POST
@require_visit
def data(request):
    form = DataForm(request.POST)
    if not form.is_valid():
        return utils.JsonHttpResponse(form.errors, status=400)

    info = form.cleaned_data
    task_key = 'map_px3_task_id_{}'.format(info['fbid'])
    px3_task_id = request.session.get(task_key, '')

    if px3_task_id:
        px3_task = celery.current_app.AsyncResult(px3_task_id)
    else:
        # Start task #

        # Extend & store Token and record authorized UserClient:
        token = facebook.client.extend_token(info['fbid'], FB_APP_ID, info['token'])
        db.delayed_save(token, overwrite=True)
        # db.get_or_create(
            # relational.UserClient,
            # client_id=client.pk, # FIXME
            # fbid=data['fbid'],
        # )
        # FIXME: Also a problem for record_event on "authorized"

        # Initiate crawl task:
        px3_task = ranking.px3_crawl.delay(token)
        request.session[task_key] = px3_task.id

    # Check status #
    if not px3_task.ready():
        return utils.JsonHttpResponse({'status': 'waiting'})

    # Check result #
    px3_edges = px3_task.result if px3_task.successful() else None
    if not px3_edges:
        return http.HttpResponseServerError('No friends were identified for you.')

    return utils.JsonHttpResponse({
        'status': 'success',
        'scores': state_scores(px3_edges).items(),
    })


@csrf_exempt
@require_http_methods(['GET', 'POST'])
@require_visit
def main(request):
    # TODO: log gimmick_map_load event?
    return render(request, 'gimmick/map.html', {
        'debug': True,
        'fb_app_id': FB_APP_ID,
    })


def max_score(network):
    score = None
    for edge in network:
        score = max(score, edge.score)
    return score


def state_scores(network, normalized=True):
    max_ = max_score(network) if normalized else 1
    scores = collections.defaultdict(int)
    # NOTE: calculate total score on backend? (and include px scores for
    # secondaries w/o state?)
    for edge in network:
        if edge.score and edge.secondary.state:
            scores[edge.secondary.state] += edge.score / max_
    return scores
