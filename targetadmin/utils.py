from django.core.exceptions import PermissionDenied
from django.contrib.auth import decorators
from django.http import HttpResponseForbidden

from targetshare import models


def superuser_required(view):
    def check_superuser(user):
        if user.is_superuser:
            return True
        raise PermissionDenied
    return decorators.user_passes_test(check_superuser)(view)


def internal(view):
    is_superuser = superuser_required(view)
    logged_in_superuser = decorators.login_required(is_superuser, login_url='login')
    return logged_in_superuser


def auth_client_required(view):
    def verify_client_auth_relation(request, *args, **kwargs):
        pk = kwargs.get('client_pk', kwargs.get('pk'))
        if (not request.user.is_superuser and
                not models.Client.objects.filter(
                    pk=pk,
                    auth_groups__in=request.user.groups.all()
                ).exists()):
                return HttpResponseForbidden(
                    'You do not have access to this area.'
                )
        return view(request, *args, **kwargs)
    return decorators.login_required(verify_client_auth_relation, login_url='login')
