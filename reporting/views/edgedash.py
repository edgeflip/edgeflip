from datetime import datetime, timedelta
from django.contrib.auth.decorators import login_required
from django.db import connections
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from targetadmin.utils import internal
from reporting.utils import isoformat_dict, run_safe_dict_query, JsonResponse

@internal
@require_http_methods(['GET', 'POST'])
def edgedash(request):
    """ 
    A very half baked visualization of all events by type 
    see internaldash.js for the front end
    """
    if request.method == 'GET':
        # render a base template
        return render(request, 'internaldash.html')
    elif request.method == 'POST':
        # load various data sets I suppose.

        # at some point let the UI configure the timespan but whatevs for right now
        tstart = request.POST.get('tstart', datetime.today() - timedelta(days=1))

        # hrm, kinda want to group by campaign_id also
        data = run_safe_dict_query(
            connections['redshift'].cursor(),
            """
            SELECT type, COUNT(event_id) as count, DATE_TRUNC('hour', event_datetime) AS hour, events.campaign_id, campaigns.name
            FROM events, campaigns
            WHERE event_datetime > %s
            AND campaigns.campaign_id=events.campaign_id
            GROUP BY hour, type, events.campaign_id, campaigns.name
            """,
            (tstart,)
        )

        data = [isoformat_dict(row, ['hour']) for row in data]
        return JsonResponse({'data':data})
