import functools

from django.shortcuts import render
from django.views.decorators.http import require_GET

from targetshare.views import utils


FB_APP_ID = 471727162864364

require_visit = functools.partial(utils.require_visit, appid=FB_APP_ID)


@require_GET
@require_visit
def data(request):
    try:
        fbid = int(request.GET['fbid'])
    except (KeyError, ValueError):
        return utils.JsonHttpResponse({'error': ['missing or invalid Facebook ID']},
                                      status=400)

    task_key = 'map_px3_task_id_{}'.format(fbid)
    px3_task_id = request.session.get(task_key, '')
    if not px3_task_id:
        # Start task
        # request.session[task_key] = ...
        return #...

    # Check status


@require_GET
@require_visit
def main(request):
    # TODO: log gimmick_map_load event?
    return render(request, 'gimmick/map.html', {
        'debug': True,
        'fb_app_id': FB_APP_ID,
    })
