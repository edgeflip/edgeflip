import json
import logging
from datetime import datetime, timedelta

from django.db import models

class CampaignSum(models.Model):
    """ all of the data for a particular campaign in daily increments """

    # ForeignKey to proper campaigns in the near future
    campaign = models.CharField(max_length=256, blank=True)
    data = models.TextField(max_length=500)  # and we jam our data in here as json

    class Meta(object):
        db_table = 'sum_campaign'

    def mkGoog(self):
        """ mangle the data field into what Google is looking for on the front end"""

        #start with a row like "2013-08-14 00:00:00": [18, 4, 3, 2, 1, 0, 0, 0, 0]
        data = json.loads( self.data)

        #make it into: {'c': [{'v': 'Date(2013,6,16)'}, {'v': 6}, {'v': 17}, {'v': 27}, {'v': 39}, {'v': 40}]}
        out = []
        for row in sorted(data.keys()):
            realday = datetime.strptime(row, "%Y-%m-%d %H:%M:%S")

            # so.. convert the string to a date, subtract 1, cast back to string :\
            day = 'Date({},{},{})'.format(realday.year, realday.month-1, realday.day)

            tmp = [{'v': v} for v in data[row]]
            tmp.insert(0, {'v':day})

            out.append( {'c':tmp})

        return out


class DaySum(models.Model):
    """ A day's worth of data in hourly increments """

    # ForeignKey to proper campaigns in the near future
    campaign = models.CharField(max_length=256, blank=True)

    day = models.DateField()
    data = models.TextField(max_length=500)  # ghetto json field .. fixed size, we could CharField here

    class Meta(object):
        db_table = 'sum_day'

    def mkGoog(self):
        """ format the data into what Google charts is looking for, basically the same format as Months """

        data = json.loads(self.data)

        out = []
        for hour, row in enumerate(data):
            tmp = [{'v':v} for v in row]
            tmp[0] = {'v':[hour,0,0]}
            #tmp.insert(0, {'v':[hour,0,0]}) 
            out.append( {'c': tmp})

        return out


