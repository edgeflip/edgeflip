from django.contrib.auth.decorators import login_required
from django.db import connections
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.utils import timezone
from logging import debug
from targetadmin.utils import internal
from reporting.utils import isoformat_row, JsonResponse

USER_COLUMNS = ['fbid', 'fname', 'lname', 'email', 'gender', 'birthday', 'city', 'state', 'updated']
EVENT_COLUMNS = ['campaign_id', 'content_id', 'friend_fbid', 'type', 'content', 'activity_id', 'updated', 'event_id', 'visit_id', 'event_datetime', 'created']
EDGE_COLUMNS = ['fbid_source', 'fbid_target', 'post_likes', 'post_comms', 'stat_likes', 'stat_comms', 'wall_posts', 'wall_comms', 'tags', 'photos_target', 'photos_other', 'mut_friends', 'updated']

@login_required(login_url='/reporting/login')
@internal
def edgeplorer(request):

  if request.method == 'GET':
    ctx = {
        'STATIC_URL':'/static/',
        'updated': timezone.now(),
    }

    return render(request, 'edgeplorer.html', ctx)
  elif request.method == 'POST':
    try:
        fbid = int(request.POST.get('fbid')) 
    except:
        raise Http404

    cursor = connections['redshift'].cursor()
    try:
        cursor.execute("""
        SELECT * FROM users WHERE fbid=%s
        """, (fbid,))
        users = [isoformat_row(zip(USER_COLUMNS, row), ['birthday','updated']) for row in cursor.fetchall()]
        debug(users)

        cursor.execute("""
        SELECT events.* FROM events,visits,visitors
        WHERE events.visit_id=visits.visit_id 
          AND visits.visitor_id=visitors.visitor_id
          AND fbid=%s 
        ORDER BY event_datetime ASC;
        """, (fbid,))
        events = [isoformat_row(zip(EVENT_COLUMNS, row), ['updated', 'event_datetime', 'created']) for row in cursor.fetchall()]
        debug(events)

        cursor.execute("""
        SELECT * FROM edges WHERE fbid_target=%s;
        """, (fbid,))
        edges = [isoformat_row(zip(EDGE_COLUMNS, row), ['updated',]) for row in cursor.fetchall()]
        debug(edges)

        return JsonResponse( {'users':users, 'events':events, 'edges':edges})
    finally:
        cursor.close()
