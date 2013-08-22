import json
import logging

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
            year, month, day = row.split(' ')[0].split('-')
            day = 'Date({},{},{})'.format( *row.split(' ')[0].split('-'))

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
            tmp.insert(0, {'v':[hour,0,0]})
            out.append( {'c': tmp})

        return out

    def mkRaph(self):
        #raphael wants a list per metric, basically
        data = json.loads(self.data)
        from collections import defaultdict
        tmp = defaultdict(lambda:[])

        for row in data:
            for i,val in enumerate(row):
                tmp[i].append(val)

        return json.dumps([[x for x in tmp[i]] for i in range(1,10)])

    def max(self):
        #for drawing axes, we need to know the maximum stacked value
        pass

        

