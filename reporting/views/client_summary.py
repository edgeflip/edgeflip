from django.core.exceptions import PermissionDenied
from django.db import connections
from django.http import Http404
from django.views.decorators.http import require_GET
from reporting.utils import run_safe_query, JsonResponse
from targetadmin.utils import auth_client_required
from targetshare.models.relational import Client


@auth_client_required
@require_GET
def client_summary(request, client_pk):
    """
    Data for the initial pageview, a summary of client stats grouped by campaign
    """

    client = Client.objects.using('mysql-readonly').get(pk=client_pk)

    if not client:
        raise Http404

    # very similar to the sums per campaign, but join on root campaign
    data = run_safe_query(
        connections['redshift'].cursor(),
        """
          SELECT meta.root_id, meta.name, visits, clicks, auths, uniq_auths,
                      shown, shares, audience, clickbacks
          FROM
              (SELECT campchain.root_id, SUM(visits) AS visits, SUM(clicks) AS clicks, SUM(auths) AS auths,
                      SUM(uniq_auths) AS uniq_auths, SUM(shown) AS shown, SUM(shares) AS shares,
                      SUM(audience) AS audience, SUM(clickbacks) AS clickbacks
                  FROM clientstats, campchain
                  WHERE campchain.parent_id=clientstats.campaign_id
                  GROUP BY root_id
              ) AS stats,

              (SELECT campchain.root_id, campaigns.campaign_id, campaigns.name 
                  FROM campaigns, campchain
                  WHERE campchain.parent_id=campaigns.campaign_id
                  AND client_id=%s
              ) AS meta

          WHERE stats.root_id=meta.campaign_id
          ORDER BY meta.root_id DESC;
        """,
         (client.client_id,)
    )
    return JsonResponse(data)
