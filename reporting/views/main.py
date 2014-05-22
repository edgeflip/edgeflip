from django.contrib.auth.decorators import login_required
from django.db.models import Max
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_GET
from targetadmin.utils import auth_client_required
from targetshare.models.relational import Client
from reporting.query import METRICS
from reporting.models.relational import Clientstats

@login_required(login_url='reporting:login')
@require_GET
def main(request):
    client_queryset = Client.objects.all()
    if not request.user.is_superuser:
        client_queryset = client_queryset.filter(auth_groups__user=request.user)

    return render(request, 'clientdash.html', {
        'updated': Clientstats.objects.aggregate(max_hour=Max('hour'))['max_hour'],
        'columns': METRICS,
        'clients': client_queryset.order_by('name').values_list('client_id', 'name'),
    })
