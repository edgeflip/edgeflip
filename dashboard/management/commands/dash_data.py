#!/usr/bin/env python
import datetime, time
import json
from navigate_db import PySql
from time import strftime

from django.conf import settings

# should be able to just do
from dashboard.models import CampaignSum, DaySum


from django.core.management.base import BaseCommand, CommandError
class Command(BaseCommand):
    def handle(self, *args, **options):

        dbcreds = settings.DASHBOARD

        global tool
        tool = PySql(dbcreds['host'], dbcreds['user'], dbcreds['secret'], dbcreds['db'])
        tool.connect()
        make_all_object()


# this will rely on Django models CampaignSum and DaySum being accessible
def make_all_object():
    all_campaigns = tool.query("select client_id, name from clients") 
    days_for_month = create_unix_time_for_each_day()
    days_for_month = [ datetime.datetime.fromtimestamp(d) for d in days_for_month ]

    all_data = all_hour_query()
    our_object = {}
    for client in all_campaigns:
        client_id = client[0]
        client_name = client[1]
        our_object[client_name] = {}
        campaigns = get_campaign_stuff_for_client(client_id)
        for campaign in campaigns:
            our_object[ client_name ][ campaign[1] ] = {}
            our_object[ client_name ][ campaign[1] ]["days"] = {}
            our_object[ client_name ][ campaign[1] ]["hours"] = {}

            # get all data that is for this campaign
            this_campaign_data = [ _set for _set in all_data if _set[0] == campaign[0] ]
            days_we_have = list( set( [ str( datetime.datetime(int(e[1]), int(e[2]), int(e[3])) ) for e in this_campaign_data ] ) )
            not_accounted_days = [
                str(datetime.datetime(d.year, d.month, d.day))
                for d in days_for_month if str(datetime.datetime(d.year, d.month, d.day)) not in days_we_have
                ]

            for day in days_we_have:
                # the day data for each day
                day_data = [
                    e for e in [
                        j[5:] for j in this_campaign_data if str(datetime.datetime(int(j[1]), int(j[2]), int(j[3]))) == day
                        ]
                    ]

                day_data_new = []
                for each in day_data:
                    day_data_new.append([ int(j) for j in each ])
                sums = []
                for i in range( len( day_data_new[0])):
                    sums.append( sum([ x[i] for x in day_data_new ]))
                our_object[client_name][ campaign[1] ]["days"][day] = sums
                # hour data portion
                hour_data = [
                    e for e in [
                        j[4:] for j in this_campaign_data if str(datetime.datetime(int(j[1]), int(j[2]), int(j[3]))) == day
                        ]
                    ]

                hour_data_new = []
                # convert our days to integers
                for each in hour_data:
                    hour_data_new.append( [ int(j) for j in each ] )
                for i in range(24):
                    if i not in [e[0] for e in hour_data_new]:
                        hour_data_new.append([i] + [0 for j in range(9)])

                #hour_data_new += [ [i] + [0 for j in range(9)] for i in range(24) if i not in [e[0] for e in hour_data_new] ] 
                our_object[ client_name ][ campaign[1] ]["hours"][day] = hour_data_new

            # for all the days over the past month that we don't have data for for the current iteration's campaign...
            for day in not_accounted_days:
                our_object[ client_name ][ campaign[1] ]["days"][day] = [ 0 for i in range(9) ]
                hour_data = [ [j] + [0 for i in range(9)] for j in range(24) ]
                our_object[ client_name ][ campaign[1] ]["hours"][day] = hour_data
    # port data to django models
    for client in our_object.keys():
        for campaign in our_object[client].keys():
            ddata = our_object[client][campaign]["days"]

            #    for k in ddata.keys():
            #        if sum(ddata[k]) == 0:
            #            del ddata[k]

            C = CampaignSum( campaign=campaign, data=json.dumps(ddata) )
            C.save()

            for day in our_object[client][campaign]["hours"].keys():
                hdata = our_object[client][campaign]["hours"][day]

                # if [sum(row) for row in hdata] == range(24): continue
                # d = datetime.strptime(d, "%Y-%m-%d %H:%M:%S")
                day = day.split(' ')[0]
                D = DaySum( campaign=campaign, data=json.dumps(hdata), day=day )
                D.save()

    print "Data successfully ported to Django Models"



"""
    This will likely be the function that is called periodically via a cron after the initial
    data scrape of all our clients and campaigns respectively.  A sort of moving window of 
    30 days of data for all campaigns and clients
"""

def keep_updated():
    this_month = create_unix_time_for_each_day()
    this_month = [ time.mktime(datetime.datetime(j.year, j.month, j.day).timetuple()) for j in [datetime.datetime.fromtimestamp(i) for i in this_month] ]
    cur_hour = strftime('%H')
    clients = tool.query("select client_id, name from clients")
    query_since = 0
    for client_id, name in clients: 
        campaigns = get_campaign_stuff_for_client(client_id)
        # call the Client class's retrieve_data method
        cur_data = Client(client_id).retrieve_data()
        # get the current month of days stored in the db
        cur_month_stored = [ i for i in cur_data[campaigns[0][1]]['days'].keys() ]
        cur_month_stored = [ time.strptime(i, "%Y-%m-%d %H:%M:%S") for i in cur_month_stored ]
        cur_month_stored = [ time.mktime(datetime.datetime(j.tm_year, j.tm_mon, j.tm_mday).timetuple()) for j in cur_month_stored ]
        new_times = [i for i in this_month if i not in cur_month_stored]
        latest_day = max(cur_month_stored)
        latest_day = str(datetime.datetime.fromtimestamp(latest_day))
        hours = [j[0] for j in cur_data[campaigns[0][1]]['hours'][latest_day]]
        break
    if hours == range(24):
        pass
    elif len(new_times) > 0:
        new_times = min(new_times)
    new_data = tool.query(main_query_hour_by_hour_new.format(new_times))
    return new_data



# SQL QUERIES

main_query_hour_by_hour_new ="""
    SELECT
        e4.campaign_id,
        YEAR(t.updated),
        MONTH(t.updated),
        DAY(t.updated),
        HOUR(t.updated),
        SUM(CASE WHEN t.type='button_load' THEN 1 ELSE 0 END) as Visits,
        SUM(CASE WHEN t.type='button_click' THEN 1 ELSE 0 END) as Clicks, 
        SUM(CASE WHEN t.type='authorized' THEN 1 ELSE 0 END) as Authorizations,
        COUNT(DISTINCT CASE WHEN t.type='authorized' THEN t.fbid ELSE NULL END) as "Distinct Facebook Users Authorized",
        COUNT(DISTINCT CASE WHEN t.type='shown' THEN t.fbid ELSE NULL END) as "# Users Shown Friends",
        COUNT(DISTINCT CASE WHEN t.type='shared' THEN t.fbid ELSE NULL END) as "# Users Who Shared",
        SUM(CASE WHEN t.type='shared' THEN 1 ELSE 0 END) as "# Friends Shared with",
        COUNT(DISTINCT CASE WHEN t.type='shared' THEN t.friend_fbid ELSE NULL END) as "# Distinct Friends Shared",
        COUNT(DISTINCT CASE WHEN t.type='clickback' THEN t.cb_session_id ELSE NULL END) as "# Clickbacks"

    FROM
        (
            SELECT e1.session_id,
                e1.campaign_id,
                e1.content_id,
                e1.ip,
                e1.fbid,
                e1.friend_fbid,
                e1.type,
                e1.appid,
                e1.content,
                e1.activity_id,
                NULL AS cb_session_id,
                e1.updated
            FROM events e1 
                WHERE type <> 'clickback' 
                AND e1.updated > NOW() - INTERVAL 1 DAY
            UNION                                                                  
            SELECT e3.session_id,
                e3.campaign_id, 
                e2.content_id,
                e2.ip,
                e3.fbid,
                e3.friend_fbid,
                e2.type,
                e2.appid,
                e2.content,
                e2.activity_id, 
                e2.session_id AS cb_session_id, 
                e2.updated
            FROM events e2 LEFT JOIN events e3 USING (activity_id)  
            WHERE e2.type='clickback' AND e3.type='shared' 
        ) t
    LEFT JOIN (SELECT session_id,campaign_id FROM events WHERE type='button_load') e4
        USING (session_id)
    GROUP BY e4.campaign_id, YEAR(t.updated), MONTH(t.updated), DAY(t.updated), HOUR(t.updated);"""

def all_hour_query():
    month = month_ago()
    res = tool.query(main_query_hour_by_hour_new.format(month))
    return res



# HELPER FUNCTIONS

def month_ago():
    one_month = 30 * 24 * 60 * 60
    return str(int(time.time())-one_month)

def get_campaign_stuff_for_client(client_id):
    res = tool.query("select campaign_id, name from campaigns where client_id='{0}' and campaign_id in (select distinct campaign_id from events where type='button_load')".format(client_id))
    return res


def create_unix_time_for_each_day():
    start = int(month_ago())
    days = []
    for i in range(30):
        start += 86400
        days.append(start)
    return days

if __name__=="__main__":
    make_all_object() 
