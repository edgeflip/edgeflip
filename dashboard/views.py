import json
from django.views.decorators.http import require_GET, require_POST
from django.shortcuts import render
from django.http import HttpResponse

from random import randint
from datetime import datetime


@require_GET
def dashboard(request):

    return render(request, 'dashboard.html')


# google.visualization is looking for this as "cols", TODO: do we actually need an id?
METRICS = [
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


def fakedata(datetime):
    """ generate fake hourly / daily data in GOOG vis format """

    # 30 days worth of data for the monthly table
    monthly = [{'c':[{'v':randint(1,100)} for i in range(len(METRICS))] } for i in range(30)]

    # 24 hours worth of data for the daily table
    daily = [{'c':[{'v':randint(1,100)} for i in range(len(METRICS))] } for i in range(25)]

    return {'cols':METRICS, 'monthly':monthly, 'daily':daily}


@require_POST
def chartdata(request):
    # look for a campaign id, default to the newest (or aggregate?)

    # look for an optional date param somehow, default to today()
    data = fakedata(datetime.today())
 
    return HttpResponse(json.dumps(data), content_type="application/json")

