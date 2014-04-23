import collections
import functools

import celery
from django import http
from django import forms
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST

from targetshare.tasks.integration.facebook import extend_token
from targetshare import models
# from targetshare.tasks import db
from targetshare.tasks import ranking
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
        # Initial call #
        token = models.datastructs.ShortToken(
            fbid=info['fbid'],
            appid=FB_APP_ID,
            token=info['token'],
        )

        # Extend & store Token:
        extend_token.delay(*token)

        # Record authorized UserClient:
        # db.get_or_create.delay(
            # relational.UserClient,
            # client_id=client.pk, # FIXME
            # fbid=data['fbid'],
        # )
        # FIXME: Also a problem for record_event on "authorized"

        # Initiate crawl task:
        px3_task = ranking.px3_crawl.delay(token, visit_id=request.visit.pk)
        request.session[task_key] = px3_task.id

    # Check status #
    if not px3_task.ready():
        return utils.JsonHttpResponse({'status': 'waiting'})

    # Check result #
    px3_edges = px3_task.result if px3_task.successful() else None
    if not px3_edges:
        return http.HttpResponseServerError('No friends were identified for you.')

    # TODO: log event?
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


def state_scores(network, normalized=True):
    """Sum the scored UserNetwork Edges' scores by state.

    By default, each Edge's score is first normalized by the network's maximum
    score.

    Returns: a dict of states and their aggregate scores.

    """
    if normalized:
        max_score = max(edge.score for edge in network)
    else:
        max_score = 1.0

    # TODO: Consider calculation
    # NOTE: also calculate total score on backend? (and include px scores
    # for secondaries w/o state?)
    scores = collections.defaultdict(int)
    for edge in network:
        if edge.score and edge.secondary.state:
            scores[edge.secondary.state] += edge.score / max_score

    return scores
