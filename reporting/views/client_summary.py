from django.core.exceptions import PermissionDenied
from django.db import connections
from django.http import Http404
from django.views.decorators.http import require_GET
from reporting.query import metric_where_fragment
from reporting.utils import run_safe_dict_query, JsonResponse
from targetadmin.utils import auth_client_required
from targetshare.models.relational import Client


@auth_client_required
@require_GET
def client_summary(request, client_pk):
    """
    Data for the initial pageview, a summary of client stats grouped by campaign
    """

    client = Client.objects.get(pk=client_pk)

    data = run_safe_dict_query(
        connections['redshift'].cursor(),
        """
        SELECT
            campaignstats.campaign_id as root_id,
            campaigns.name,
            max(latest_activity) as latest_activity,
            min(first_activity) as first_activity,
            {}
        FROM campaignstats
        JOIN campaigns using (campaign_id)
        JOIN (
            select
                campaign_id,
                to_char(max(hour), 'YYYY-MM-DD') as latest_activity,
                to_char(min(hour), 'YYYY-MM-DD') as first_activity
                from clientstats group by campaign_id
            ) as timelookup using (campaign_id)
        WHERE campaigns.client_id = %s
        GROUP BY campaignstats.campaign_id, campaigns.name
        """.format(metric_where_fragment()),
         (client.client_id,)
    )

    rollup_data = run_safe_dict_query(
        connections['redshift'].cursor(),
        """
        SELECT
        {}
        FROM clientrollups
        WHERE client_id = %s
        """.format(metric_where_fragment()),
        (client.client_id,)
    )

    return JsonResponse({'data': data, 'rollups': rollup_data})
