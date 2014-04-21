import csv
from django.db import connections
from django.http import HttpResponse
from django.views.decorators.http import require_GET
from targetadmin.utils import auth_client_required
from reporting.utils import isoformat_dict, isoformat_row, run_safe_dict_query, run_safe_row_query, JsonResponse


@auth_client_required
@require_GET
def campaign_hourly(request, client_pk, campaign_pk):
    """ Data for a particular campaign, used by the chart view """

    query = """
        SELECT
            date_trunc('hour', hour) as time,
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
        WHERE campaigns.campaign_id = %s
        GROUP BY time
        ORDER BY time ASC
        """
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
        return generate_csv(data)
    else:
        data = run_safe_dict_query(
            cursor,
            query,
            (campaign_pk,)
        )
        return JsonResponse({'data':[isoformat_dict(row) for row in data]})


def generate_csv(data):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="somefilename.csv"'
    writer = csv.writer(response)
    for row in data:
        writer.writerow(row)
    return response
