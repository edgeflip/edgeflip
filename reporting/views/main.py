from django.contrib.auth.decorators import login_required
from django.db import connections
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_GET
from targetshare.models.relational import Client

@login_required(login_url='/reporting/login')
@require_GET
def main(request):
    ctx = {
        'updated': timezone.now()
    }

    # if it's a superuser, look up the clients to populate the chooser
    if request.user.is_superuser:
        ctx['clients'] = Client.objects \
            .using('mysql-readonly') \
            .order_by('-client_id') \
            .values_list('client_id', 'name')

    return render(request, 'clientdash.html', ctx)
