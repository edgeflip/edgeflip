import csv
from datetime import datetime
from django.db import connections
from django.http import HttpResponse
from django.views.decorators.http import require_GET
from targetadmin.utils import auth_client_required
from targetshare.models import Client
from reporting.query import metric_where_fragment
from reporting.utils import isoformat_dict, isoformat_row, run_safe_dict_query, run_safe_row_query, JsonResponse


@auth_client_required
@require_GET
def campaign_hourly(request, client_pk, campaign_pk):
    """ Data for a particular campaign, used by the chart view """

    query = """
        SELECT
            date_trunc('hour', hour) as time,
            {}
        FROM clientstats
        JOIN campaigns using (campaign_id)
        WHERE campaigns.campaign_id = %s
        GROUP BY time
        ORDER BY time ASC
        """.format(metric_where_fragment())
    cursor = connections['redshift'].cursor()

    response_format = request.GET.get('format', '')
    if response_format == 'csv':
        data = run_safe_row_query(
            cursor,
            query,
            (campaign_pk,)
        )
        data = [isoformat_row(row, [0]) for row in data]
        data.insert(0, [col.name for col in cursor.description])
        return generate_csv(data, client_pk)
    else:
        data = run_safe_dict_query(
            cursor,
            query,
            (campaign_pk,)
        )
        return JsonResponse({'data':[isoformat_dict(row) for row in data]})


def generate_csv(data, client_pk):
    client = Client.objects.only('codename').get(pk=client_pk)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="{}-report-{}.csv"'.format(client.codename, datetime.today().strftime('%Y-%m-%dT%H:%M:%S'))
    writer = csv.writer(response)
    for row in data:
        writer.writerow(row)
    return response
