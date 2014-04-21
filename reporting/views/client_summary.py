from django.core.exceptions import PermissionDenied
from django.db import connections
from django.http import Http404
from django.views.decorators.http import require_GET
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
            clientstats.campaign_id as root_id,
            campaigns.name,
            SUM(visits) AS visits,
            SUM(authorized_visits) as authorized_visits,
            SUM(uniq_users_authorized) as uniq_users_authorized,
            SUM(auth_fails) as auth_fails,
            SUM(visits_generated_faces) as visits_generated_faces,
            SUM(visits_shown_faces) as visits_shown_faces,
            SUM(visits_with_shares) as visits_with_shares,
            SUM(total_shares) AS total_shares,
            SUM(clickbacks) AS clickbacks
        FROM clientstats
        JOIN campaigns using (campaign_id)
        WHERE campaigns.client_id = %s
        GROUP BY clientstats.campaign_id, campaigns.name
        """,
         (client.client_id,)
    )

    rollup_data = run_safe_dict_query(
        connections['redshift'].cursor(),
        """
        SELECT
            SUM(visits) AS visits,
            SUM(authorized_visits) as authorized_visits,
            SUM(uniq_users_authorized) as uniq_users_authorized,
            SUM(auth_fails) as auth_fails,
            SUM(visits_generated_faces) as visits_generated_faces,
            SUM(visits_shown_faces) as visits_shown_faces,
            SUM(visits_with_shares) as visits_with_shares,
            SUM(total_shares) AS total_shares,
            SUM(clickbacks) AS clickbacks
        FROM clientrollups
        WHERE client_id = %s
        """,
        (client.client_id,)
    )

    return JsonResponse({'data': data, 'rollups': rollup_data})
