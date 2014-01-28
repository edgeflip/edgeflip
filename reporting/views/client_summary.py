from django.core.exceptions import PermissionDenied
from django.db import connections
from reporting.utils import JsonResponse
from targetadmin.utils import auth_client_required
from targetshare.models.relational import Client

HEADER = ['root_id', 'name', 'visits', 'clicks', 'auths', 'uniq_auths', 'shown', 'shares', 'audience', 'clickbacks']

@auth_client_required
def client_summary(request, client_pk):
    """
    Data for the initial pageview, a summary of client stats grouped by campaign
    """
    client = Client.objects.using('mysql-readonly').get(pk=client_pk)

    if not client:
        # check authorization for arbitrary client ids
        if not request.user.is_superuser: raise PermissionDenied

    # very similar to the sums per campaign, but join on root campaign
    cursor = connections['redshift'].cursor()
    try:
        cursor.execute("""
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
        """, (int(client.client_id),))
        return JsonResponse([dict(zip(HEADER, row)) for row in cursor.fetchall()])
    finally:
        cursor.close()
