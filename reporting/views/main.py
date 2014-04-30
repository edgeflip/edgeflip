from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_GET
from targetadmin.utils import auth_client_required
from targetshare.models.relational import Client
from reporting.query import METRICS

@login_required(login_url='reporting:login')
@require_GET
def main(request):
    client_queryset = Client.objects.all()
    if not request.user.is_superuser:
        client_queryset = client_queryset.filter(auth_groups__user=request.user)

    return render(request, 'clientdash.html', {
        'updated': timezone.now(),
        'columns': METRICS,
        'clients': client_queryset.order_by('name').values_list('client_id', 'name'),
    })
