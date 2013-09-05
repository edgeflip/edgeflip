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

        self.pcur.execute( """
        SELECT * FROM information_schema.tables WHERE table_schema='public' AND table_name='sum_day';
        """)

        if not self.pcur.fetchall():
            self.pcur.execute("""
            CREATE TABLE sum_day (
                campaign_id INTEGER,
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

        megaquery = """

    CREATE TABLE clientstats AS 
    SELECT 
        e4.campaign_id,
        date_trunc('hour', t.updated) as time,
        SUM(CASE WHEN t.type='button_load' THEN 1 ELSE 0 END) AS visits,
        SUM(CASE WHEN t.type='button_click' THEN 1 ELSE 0 END) AS clicks,
        SUM(CASE WHEN t.type='authorized' THEN 1 ELSE 0 END) AS auths,
        COUNT(DISTINCT CASE WHEN t.type='authorized' THEN t.fbid ELSE NULL END) AS uniq_auths,
        COUNT(DISTINCT CASE WHEN t.type='shown' THEN t.fbid ELSE NULL END) AS shown,
        COUNT(DISTINCT CASE WHEN t.type='shared' THEN t.fbid ELSE NULL END) AS shares,
        COUNT(DISTINCT CASE WHEN t.type='shared' THEN t.friend_fbid ELSE NULL END) AS audience,
        COUNT(DISTINCT CASE WHEN t.type='clickback' THEN t.cb_session_id ELSE NULL END) AS clickbacks

    FROM
        (
            SELECT e1.session_id, e1.campaign_id, e1.content_id, e1.ip, e1.fbid, e1.friend_fbid,
                e1.type, e1.appid, e1.content, e1.activity_id, NULL AS cb_session_id, e1.updated
            FROM events e1
                WHERE type <> 'clickback'
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
    GROUP BY e4.campaign_id, date_trunc('hour', t.updated);
        """

    # GROUP BY e4.campaign_id, extract(year from t.updated), extract(month from t.updated), extract(day from t.updated);

"""
    CREATE TABLE foo AS
    SELECT
        to_timestamp( (
            cast(extract(year FROM now()) as text) 
                ||' '||
            cast(extract(month from now()) as text) 
                ||' '||
            cast(extract(day from now()) as text)
                ||' '||
            cast(extract(hour from now()) as text)
            ), 'YYYY MM DD HH24') as time,
"""

