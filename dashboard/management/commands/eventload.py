import MySQLdb as mysql
import psycopg2
from time import time
from datetime import datetime
from logging import debug, info, warning
from django.conf import settings


from django.core.management.base import BaseCommand, CommandError
class Command(BaseCommand):

    # @transaction.commit_on_success
    def handle(self, *args, **options):
        self.tstart = time()

        dbcreds = settings.DASHBOARD

        self.mconn = mysql.connect(dbcreds['host'], dbcreds['user'], dbcreds['secret'], dbcreds['db'])
        self.mcur = self.mconn.cursor(mysql.cursors.DictCursor)

        self.pconn = psycopg2.connect(host='wes-rs-inst.cd5t1q8wfrkk.us-east-1.redshift.amazonaws.com',
            user='edgeflip', database='edgeflip', port=5439, password='XzriGDp2FfVy9K')
        self.pcur = self.pconn.cursor()

        self.mktables()
        self.get_events()

        info( "Summary tables completed in {}".format(time()-self.tstart))


    def mktables(self):
        self.pcur.execute( """
        SELECT * FROM information_schema.tables WHERE table_schema='public' AND table_name='events';
        """)

        if not self.pcur.fetchall():
            self.pcur.execute("""
            CREATE TABLE events (
                session_id VARCHAR(128),
                campaign_id INTEGER,
                content_id INTEGER,
                ip VARCHAR(32),
                fbid BIGINT,
                friend_fbid BIGINT,
                type VARCHAR(128),
                appid BIGINT,
                content VARCHAR(128), 
                activity_id BIGINT,
                updated TIMESTAMP
                )
            """)

    def get_events(self):
        tstart = time()
        rowcount = 0

        # we want to get whatever we don't have so check what we have:
        self.pcur.execute("""SELECT updated FROM events ORDER BY updated DESC LIMIT 1;""")
        response = self.pcur.fetchone()
        if not response:
            d = datetime(2013,1,1)
        else:
            d = response[0]

        self.mcur.execute("SELECT * FROM events WHERE updated > %s ORDER BY updated ASC", d)

        def load(row):
            self.pcur.execute(""" INSERT INTO events (activity_id, appid, campaign_id, content, 
                content_id, fbid, friend_fbid, ip, session_id, type, updated)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, tuple([row[k] for k in sorted(row.keys())]))

        # load one at a time with fetchone() to keep mem usage on mysql
        row = self.mcur.fetchone()
        while row:
            load(row)
            row = self.mcur.fetchone()
            rowcount += 1
            if not rowcount % 100:
                elapsed = time()-tstart
                info('row #{} in {} ( {}row/s)'.format(rowcount, elapsed, (rowcount/elapsed) ))

        self.pconn.commit()

        info( "{} events synced in {}".format(rowcount, time()-tstart))


    def mksummary(self):
        """ 
        in theory we'd know which events we just added and could recalc summary tables atomically
        """
        import pdb;pdb.set_trace()



