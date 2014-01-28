from django.db import connections
from targetadmin.utils import auth_client_required
from reporting.utils import isoformat_row, JsonResponse

HEADER = ['time', 'visits', 'clicks', 'auths', 'uniq_auths', 'shown', 'shares', 'audience', 'clickbacks']

@auth_client_required
def campaign_hourly(request, client_pk, campaign_pk):
    """ Data for a particular campaign, used by the chart view """

    cursor = connections['redshift'].cursor()
    try:
        cursor.execute("""
        SELECT DATE_TRUNC('hour', hour) as time,
            SUM(visits) AS visits,
            SUM(clicks) AS clicks,
            SUM(auths) AS auths,
            SUM(uniq_auths) AS uniq_auths,
            SUM(shown) AS shown,
            SUM(shares) AS shares,
            SUM(audience) AS audience,
            SUM(clickbacks) AS clickbacks
            
        FROM clientstats,campchain 
        WHERE clientstats.campaign_id=campchain.parent_id
        AND campchain.root_id=%s
        GROUP BY time
        ORDER BY time ASC
        """, (campaign_pk,))

        data = [isoformat_row(dict(zip(HEADER, row))) for row in cursor.fetchall()]
        return JsonResponse({'data':data})
    finally:
        cursor.close()
