import MySQLdb as mysql
import psycopg2
from time import time
from logging import debug, info, warning
from django.conf import settings


from django.core.management.base import BaseCommand, CommandError
class Command(BaseCommand):

    # @transaction.commit_on_success
    def handle(self, *args, **options):
        self.tstart = time()

        
        dbcreds = settings.DASHBOARD
        # self.mconn = mysql.connect(dbcreds['host'], dbcreds['user'], dbcreds['secret'], dbcreds['db'])
        # self.mcur = self.mconn.cursor(mysql.cursors.DictCursor)
        dbcreds['port'] = 5439

        self.pconn = psycopg2.connect( **dbcreds)
        self.pcur = self.pconn.cursor()

        self.mksummary()

        info( "Summary tables completed in {}".format(time()-self.tstart))


    def mksummary(self):

        self.pcur.execute("DROP TABLE clientstats")

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

        self.pcur.execute(megaquery)

        self.pconn.commit()

