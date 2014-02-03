from django.db import connections
from django.views.decorators.http import require_GET
from targetadmin.utils import auth_client_required
from reporting.utils import isoformat_row, run_safe_query, JsonResponse


@auth_client_required
@require_GET
def campaign_hourly(request, client_pk, campaign_pk):
    """ Data for a particular campaign, used by the chart view """

    data = run_safe_query(
        connections['redshift'].cursor(),
        """
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
        """,
        (campaign_pk,)
    )

    data = [isoformat_row(row) for row in data]
    return JsonResponse({'data':data})
