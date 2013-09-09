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


def date2goog(dt):
    # make the date this goofy ass 0 based string
    return 'Date({},{},{})'.format(dt.year, dt.month-1, dt.day)


@require_GET
@login_required(login_url='/dashboard/login/')
def dashboard(request):

    # so normally.. look up campaigns available to this user.
    # for now, we have only one client with data, so:

    pconn = psycopg2.connect(host='wes-rs-inst.cd5t1q8wfrkk.us-east-1.redshift.amazonaws.com',
            user='edgeflip', database='edgeflip', port=5439, password='XzriGDp2FfVy9K')
    pcur = pconn.cursor(cursor_factory = psycopg2.extras.DictCursor)
    # campaigns = [row.campaign for row in CampaignSum.objects.all()]
    pcur.execute("""
        SELECT campaign_id, name FROM campaigns WHERE client_id=2 AND campaign_id IN 
            (SELECT DISTINCT(campaign_id) FROM events WHERE type='button_load')
        """)
    campaigns = pcur.fetchall() 
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


def sum_campaign(data):
    out = []  # the final list of data points

    day = data[0][1]  # to track what day we're building
    tmp = []  # stuff everything in here then sum

    def sumday(row, tmp, day):
        """ on to tomorrow, sum tmp, append it and start a new day """
        daysum = [sum(i) for i in zip(*tmp)]
        daysum.insert(0, date2goog(day))  # set the day's timestamp in goog format
        daysum = [{'v':v} for v in daysum]
        daysum = {'c':daysum}

        #set up the new day and move on 
        day = row[1]
        tmp = [row[2:],]

        return daysum, tmp, day

    for row in data:
        """ hrm.. see the defaultdict approach below for a probably much easier approach """
        tdelta = row[1]-day
        if tdelta.days == 0:
            # hourly data to be added to this day's row
            tmp.append(row[2:])

        elif tdelta.days == 1:
            daysum,tmp,day = sumday(row,tmp,day)
            out.append(daysum)

        elif tdelta.days > 1:
            # gaps in the daily data!

            # close out the day
            _day = day
            daysum,tmp,day = sumday(row,tmp,day)
            out.append(daysum)

            #pad with zeros
            for i in range(tdelta.days-1):
                daysum = [date2goog( _day + timedelta(days=i+1)),]
                daysum += [0 for j in range(8)]  # TODO: link this to length of metrics
                daysum = [{'v':v} for v in daysum]
                daysum = {'c':daysum}
                out.append(daysum)

    return out 


from collections import defaultdict
def pad_day(data, day):
    """ pull out the data for just this day, pad with zeros for the off hours """
    data = [r for r in data if (r[1]-day).days == 0]

    hours = defaultdict(lambda: [{'v':0} for j in range(8)])
    for row in data:
        # index the data we have by hour basically
        hours[row[1].hour] = [{'v':v} for v in row[2:]]  # and throw out the campaign_id / timestamp

    out = [[{'v':[i,0,0]},]+hours[i] for i in range(0,24)]  # grab the default and set the time at [0]
    out = [{'c':i} for i in out]

    return out


def chartdata(request):

    out = {}

    # check for an aggregate request
    if ('campaign' in request.POST) and (request.POST['campaign'] == 'aggregate'):
        return aggregate(request)

    pconn = psycopg2.connect(host='wes-rs-inst.cd5t1q8wfrkk.us-east-1.redshift.amazonaws.com',
            user='edgeflip', database='edgeflip', port=5439, password='XzriGDp2FfVy9K')
    pcur = pconn.cursor(cursor_factory = psycopg2.extras.DictCursor)

    # minor security hole/TODO: make sure the user is authorized to request stats for this campaign
    camp_id = int(request.POST['campaign'])  # and.. hope psycopg2 checking for sql injection
  
    # join, but really just send the campaign id from the client side 
    # pcur.execute("""SELECT campaign_id, client_id FROM campaigns WHERE name=%s""", (camp_name,)) 
    # camp_id = pcur.fetchone()[0]
    
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
       
        # we should do this but.. the day comes in as midnight, so the min/max comp fails 
        # if not minday <= d <= maxday:
        #    d = maxday
    else:
        d = maxday

    # pad our data with zeros, stuff it into google format
    out['monthly'] = sum_campaign(data)
    out['dailyday'] = d.strftime( '%m/%d/%y')
    out['daily'] = pad_day(data, d)
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
