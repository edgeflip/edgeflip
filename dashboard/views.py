import json
from django.views.decorators.http import require_GET, require_POST
from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

from random import randint
from datetime import datetime, timedelta


@require_GET
@login_required(login_url='/dashboard/login/')
def dashboard(request):
    user = request.user  # really seems like this should automagically happen

    context = {
        'user': user,
        'campaigns': [],
        }

    return render(request, 'dashboard.html', context)


# google.visualization is looking for this as "cols", TODO: do we actually need an id?
MONTHLY_METRICS = [
    {'id': 'label', 'label': 'time', 'type': 'date'},  # this wants to be timeofday for hourly, day for monthly
    {'id': 'visits', 'label': 'Visits', 'type': 'number'},
    {'id': 'clicks', 'label': 'Clicks', 'type': 'number'},
    {'id': 'auths', 'label': 'Authorizations', 'type': 'number'},
    {'id': 'uniq_auths', 'label': 'Unique Authorizations', 'type': 'number'},
    {'id': 'shown_friends', 'label': 'Users Shown Friends', 'type': 'number'},
    {'id': 'shares', 'label': 'Users Who Shared', 'type': 'number'},
    {'id': 'share_reach', 'label': 'Friends Shared With', 'type': 'number'},
    {'id': 'uniq_share_reach', 'label': 'Unique Friends Shared With', 'type': 'number'},
    {'id': 'clickbacks', 'label': 'Clickbacks', 'type': 'number'},
    ]

DAILY_METRICS = [{'id':'label', 'label': 'time', 'type':'timeofday'},] + MONTHLY_METRICS[1:]

def fakedata(now):
    """ generate fake hourly / daily data in GOOG vis format """

    # 30 days worth of data for the monthly table
    monthly = [{'c':[{'v':randint((i*10),((i*10)+9))} for i in range(len(MONTHLY_METRICS))] } for j in range(30)]

    """ 
    to get the chart to draw right, even though the data is ordered, the first element in each
    row needs to be set in order:  TODO, make these actual ... days / hours
    """
    for i in range(30):
        delta = timedelta(days=(30-i))
        monthly[i]['c'].insert(0, {'v':"Date({},{},{})".format(now.year, (now-delta).month-1, (now-delta).day)}  )
        
    # import pdb;pdb.set_trace()

    # 24 hours worth of data for the daily table
    daily = [{'c':[{'v':randint(1,100)} for i in range(len(MONTHLY_METRICS))] } for j in range(25)]
    for i in range(25):
        daily[i]['c'].insert(0, {'v':[i,0,0]})

    return {'monthly_cols':MONTHLY_METRICS, 'daily_cols':DAILY_METRICS, 'monthly':monthly, 'daily':daily}


@require_POST
@login_required(login_url='/dashboard/login/')
def chartdata(request):
    # look for a campaign id, default to the newest (or aggregate?)


    if 'day' in request.POST and request.POST['day']:
        #catch errors on this as malicious POSTs
        t = datetime.strptime( request.POST['day'], '%m/%d/%Y')
    else:
        t = datetime.today()

    data = fakedata(t)
 
    return HttpResponse(json.dumps(data), content_type="application/json")

