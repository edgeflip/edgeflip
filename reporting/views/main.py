from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_GET
from targetadmin.utils import auth_client_required
from targetshare.models.relational import Client

@login_required(login_url='reporting:login')
@require_GET
def main(request):
    client_queryset = Client.objects.all()
    if not request.user.is_superuser:
        client_queryset = client_queryset.filter(auth_groups__user=request.user)

    columns = [
        ('visits', 'Visits', '# of unique visits'),
        ('authorized_visits', 'Authorized Visits', '# of visits that authorized'),
        ('uniq_users_authorized', 'Users Authorized', '# of unique users who authorized'),
        ('auth_fails', 'Authorization Fails', '# of failed authorizations (either via decline or error)'),
        ('visits_generated_faces', 'Visits Generated Faces', '# of visits that had friend suggestions generated'),
        ('visits_shown_faces', 'Visits Shown Faces', '# of visits that had friend suggestions shown to them'),
        ('visits_with_shares', 'Visits With Shares', '# of visits that had at least one share'),
        ('total_shares', 'Total Shares', '# of total shares'),
        ('clickbacks', 'Clickbacks', '# of total clickbacks'),
    ]
    return render(request, 'clientdash.html', {
        'updated': timezone.now(),
        'columns': columns,
        'clients': client_queryset.order_by('name').values_list('client_id', 'name'),
    })
