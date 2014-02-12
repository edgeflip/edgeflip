from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_GET
from targetadmin.utils import auth_client_required
from targetshare.models.relational import Client

@login_required(login_url='reporting:login')
@require_GET
def main(request):
    ctx = {
        'updated': timezone.now()
    }

    clients = Client.objects
    if not request.user.is_superuser:
        clients = clients.filter(auth_groups__user=request.user)
    ctx['clients'] = clients.order_by('-client_id').values_list('client_id', 'name')

    return render(request, 'clientdash.html', ctx)
