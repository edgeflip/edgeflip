from django.db import connections
from django.db.models import Max
from django.views.decorators.http import require_GET
from reporting.models import Campaignhourly
from reporting.query import metric_where_fragment
from reporting.utils import run_safe_dict_query, JsonResponse, cached_report
from targetadmin.utils import auth_client_required
from targetshare.models.relational import Client


@auth_client_required
@require_GET
def client_summary(request, client_pk):
    """
    Data for the initial pageview, a summary of client stats grouped by campaign
    """

    client = Client.objects.get(pk=client_pk)

    def retrieve_campaign_rollups():
        return run_safe_dict_query(
            connections['reporting'].cursor(),
            """
            SELECT
                campaignrollups.campaign_id as root_id,
                campaigns.name,
                max(latest_activity) as latest_activity,
                min(first_activity) as first_activity,
                {}
            FROM campaignrollups
            JOIN campaigns using (campaign_id)
            JOIN (
                select
                    campaign_id,
                    to_char(max(hour), 'YYYY-MM-DD') as latest_activity,
                    to_char(min(hour), 'YYYY-MM-DD') as first_activity
                    from campaignhourly group by campaign_id
                ) as timelookup using (campaign_id)
            WHERE campaigns.client_id = %s
            GROUP BY campaignrollups.campaign_id, campaigns.name
            ORDER BY campaignrollups.campaign_id desc
            """.format(metric_where_fragment()),
            (client.client_id,)
        )

    def retrieve_client_rollups():
        return run_safe_dict_query(
            connections['reporting'].cursor(),
            """
            SELECT
            {}
            FROM clientrollups
            WHERE client_id = %s
            """.format(metric_where_fragment()),
            (client.client_id,)
        )

    def retrieve_client_lastdata():
        return Campaignhourly.objects \
            .filter(campaign__client_id=client.client_id) \
            .aggregate(max_hour=Max('hour'))['max_hour']

    data = cached_report(
        'campaignrollups',
        client.client_id,
        retrieve_campaign_rollups
    )

    rollup_data = cached_report(
        'clientrollups',
        client.client_id,
        retrieve_client_rollups
    )

    last_updated = cached_report(
        'clientlastdata',
        client.client_id,
        retrieve_client_lastdata
    )

    return JsonResponse({
        'data': data,
        'rollups': rollup_data,
        'lastupdated': last_updated
    })
