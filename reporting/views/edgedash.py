from datetime import datetime, timedelta
from django.contrib.auth.decorators import login_required
from django.db import connections
from django.http import HttpResponse
from django.shortcuts import render
from targetadmin.utils import internal
from reporting.utils import isoformat_row, JsonResponse

COLUMNS = ['type', 'count', 'hour', 'campaign_id', 'name']

@login_required(login_url='/reporting/login')
@internal
def edgedash(request):
    """ 
    A very half baked visualization of all events by type 
    see internaldash.js for the front end
    """
    if request.method == 'GET':
        # render a base template
        ctx = {
            'STATIC_URL':'/static/',
        }

        return render(request, 'internaldash.html', ctx)
    elif request.method == 'POST':
        # load various data sets I suppose.

        # at some point let the UI configure the timespan but whatevs for right now
        tstart = request.POST.get('tstart', datetime.today() - timedelta(days=1))

        # hrm, kinda want to group by campaign_id also
        cursor = connections['redshift'].cursor()
        try:
            cursor.execute("""
            SELECT type, COUNT(event_id) as count, DATE_TRUNC('hour', event_datetime) AS hour, events.campaign_id, campaigns.name
            FROM events, campaigns
            WHERE event_datetime > %s
            AND campaigns.campaign_id=events.campaign_id
            GROUP BY hour, type, events.campaign_id, campaigns.name
            """, (tstart,))

            data = [isoformat_row(zip(COLUMNS, row), ['hour']) for row in cursor.fetchall()]
            return JsonResponse({'data':data})
        finally:
            cursor.close()
