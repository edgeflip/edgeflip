import json
import logging
from random import randint
from datetime import datetime, timedelta

from django.views.decorators.http import require_GET, require_POST
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout

from models import CampaignSum, DaySum

import psycopg2
import psycopg2.extras

def dashlogout(request):
    logout(request)

    return redirect('/dashboard/login/')


@require_GET
@login_required(login_url='/dashboard/login/')
def dashboard(request):

    # so normally.. look up campaigns available to this user.
    # for now, we have only one client with data, so:
    campaigns = [row.campaign for row in CampaignSum.objects.all()]


    user = request.user  # really seems like this should automagically happen
    context = {
        'user': user,
        'campaigns': campaigns,
        }

    return render(request, 'dashboard/dashboard.html', context)


# google.visualization is looking for this as "cols", TODO: do we actually need an id?
MONTHLY_METRICS = [
    {'id': 'label', 'label': 'time', 'type': 'date'},  # this wants to be timeofday for hourly, day for monthly
    {'id': 'visits', 'label': 'Visits', 'type': 'number'},
    {'id': 'clicks', 'label': 'Clicks', 'type': 'number'},
    {'id': 'auths', 'label': 'Authorizations', 'type': 'number'},
    {'id': 'uniq_auths', 'label': 'Unique Authorizations', 'type': 'number'},
    {'id': 'shown', 'label': 'Users Shown Friends', 'type': 'number'},
    {'id': 'shares', 'label': 'Users Who Shared', 'type': 'number'},
    {'id': 'audience', 'label': 'Unique Friends Shared With', 'type': 'number'},
    {'id': 'clickbacks', 'label': 'Clickbacks', 'type': 'number'},
    ]

DAILY_METRICS = [{'id':'label', 'label': 'time', 'type':'timeofday'},] + MONTHLY_METRICS[1:]

def fakedata(now, client_id=None):
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
        
    # 24 hours worth of data for the daily table
    daily = [{'c':[{'v':randint(1,100)} for i in range(len(MONTHLY_METRICS))] } for j in range(25)]
    for i in range(25):
        daily[i]['c'].insert(0, {'v':[i,0,0]})

    return {'monthly_cols':MONTHLY_METRICS, 'daily_cols':DAILY_METRICS, 'monthly':monthly, 'daily':daily}


def chartdata(request):

    out = {}

    # check for an aggregate request
    if ('campaign' in request.POST) and (request.POST['campaign'] == 'aggregate'):
        return aggregate(request)

    pconn = psycopg2.connect(host='wes-rs-inst.cd5t1q8wfrkk.us-east-1.redshift.amazonaws.com',
            user='edgeflip', database='edgeflip', port=5439, password='XzriGDp2FfVy9K')
    pcur = pconn.cursor(cursor_factory = psycopg2.extras.DictCursor)

    # minor security hole/TODO: make sure the user is authorized to request stats for this campaign
    camp_name = request.POST['campaign']  # and.. hope psycopg2 checking for sql injection
  
    # join, but really just send the campaign id from the client side 
    pcur.execute("""SELECT campaign_id, client_id FROM campaigns WHERE name=%s""", (camp_name,)) 
    camp_id = pcur.fetchone()[0]
    
    pcur.execute("""SELECT * FROM clientstats WHERE campaign_id=%s ORDER BY time ASC""",(camp_id,))
    data = [row for row in pcur.fetchall()]

    days = [row[1] for row in data]


    # find min and max days ... this needs to be elsewhere
    minday,maxday = min(days), max(days)

    # send min and max days to restrict selectable days in the jquery widget
    out['minday'] = minday.strftime( '%m/%d/%y')
    out['maxday'] = maxday.strftime( '%m/%d/%y')

    # pick the day we're going to look up data for, by POST or default
    if 'day' in request.POST and request.POST['day']:
        #catch errors on this as malicious POSTs
        d = datetime.strptime( request.POST['day'], '%m/%d/%Y')
        if not minday < d < maxday:
            d = maxday
    else:
        d = maxday

    def date2goog(dt):
        # make the date this goofy ass 0 based string
        return 'Date({},{},{})'.format(dt.year, dt.month-1, dt.day)

    import pdb;pdb.set_trace()


@require_POST
@login_required(login_url='/dashboard/login/')
def oldchartdata(request):

    out = {}

    # check for an aggregate request
    if ('campaign' in request.POST) and (request.POST['campaign'] == 'aggregate'):
        return aggregate(request)

    # look for a campaign id, default is whatever order we load the template
    monthly = CampaignSum.objects.get(campaign=request.POST['campaign'])
    out['monthly'] = monthly.mkGoog()

    # grab min and max dates, TODO: this should be in the summary table
    monthdata = json.loads( monthly.data)
    days = [datetime.strptime(day, "%Y-%m-%d %H:%M:%S") for day in monthdata.keys()]
    minday,maxday = min(days), max(days)

    # send min and max days to restrict selectable days in the jquery widget
    out['minday'] = minday.strftime( '%m/%d/%y')
    out['maxday'] = maxday.strftime( '%m/%d/%y')

    """
    sometimes there are gaps in the data, but jquery only lets us limit between one set
    of dates!  so, if we don't have the Day object, just send back zeros
    """
    try:
        daily = DaySum.objects.get(day=t, campaign=monthly.campaign)
        out['daily'] = daily.mkGoog()
        out['dailyday'] = daily.day.strftime( '%m/%d/%y')
    except DaySum.DoesNotExist:
        blah = []
        for i in range(24):
            r = [{'v':0} for i in range(10)]
            r[0] = {'v':[i,0,0]}
            blah.append(r)
        out['daily'] = [{'c':blah}]
        out['dailyday'] = t.strftime( '%m/%d/%y')

    out['monthly_cols'] = MONTHLY_METRICS
    out['daily_cols'] = DAILY_METRICS

    return HttpResponse(json.dumps(out), content_type="application/json")


def aggregate(request):
    aggdata = []
    for row in CampaignSum.objects.all():
        googdata = [{'v':row.campaign},] + [{'v':sum(i)} for i in zip(*json.loads(row.data).values())] 
        if len(googdata) == 10:
            aggdata.append( {'c':googdata} )

    metrics = MONTHLY_METRICS[:]
    metrics[0] = {'type':'string', 'id':'campname', 'label':'Campaign Name'}

    out = {'cols': metrics, 'rows': aggdata}

    return HttpResponse(json.dumps(out), content_type="application/json")


def mkdata(request):
    """one off that should be a management command to dump wes's json into django"""

    from dash_data import make_all_object
    make_all_object()

