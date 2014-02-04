from django.contrib.auth.decorators import login_required
from django.db import connections
from django.http import HttpResponseBadRequest
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from logging import debug
from targetadmin.utils import internal
from reporting.utils import isoformat_row, run_safe_query, JsonResponse

@internal
@require_http_methods(['GET', 'POST'])
def edgeplorer(request):

  if request.method == 'GET':
    ctx = {
        'updated': timezone.now(),
    }

    return render(request, 'edgeplorer.html', ctx)
  elif request.method == 'POST':
    try:
        fbid = int(request.POST['fbid']) 
    except (KeyError, ValueError):
        return HttpResponseBadRequest('fbid missing or badly formed')

    users = run_safe_query(
        connections['redshift'].cursor(),
        'SELECT * FROM users WHERE fbid=%s',
        (fbid,)
    )
    users = [isoformat_row(row, ['birthday','updated']) for row in users]
    debug(users)

    events = run_safe_query(
        connections['redshift'].cursor(),
        """
        SELECT events.* FROM events,visits,visitors
        WHERE events.visit_id=visits.visit_id 
          AND visits.visitor_id=visitors.visitor_id
          AND fbid=%s 
        ORDER BY event_datetime ASC;
        """,
         (fbid,)
    )
    events = [isoformat_row(row, ['updated', 'event_datetime', 'created']) for row in events]
    debug(events)

    edges = run_safe_query(
        connections['redshift'].cursor(),
        'SELECT * FROM edges WHERE fbid_target=%s',
        (fbid,)
    )
    edges = [isoformat_row(row, ['updated',]) for row in edges]
    debug(edges)

    return JsonResponse( {'users':users, 'events':events, 'edges':edges})
