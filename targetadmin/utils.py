import functools

from django.utils.decorators import method_decorator
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


# We could remove the internal decorator. I could see it being useful for
# superuser only views, but we don't really have any of these now.
def internal(view):
    is_superuser = superuser_required(view)
    logged_in_superuser = decorators.login_required(is_superuser, login_url='login')
    return logged_in_superuser


def auth_client_required(view):
    @functools.wraps(view)
    @decorators.login_required(login_url='login')
    def verify_client_auth_relation(request, *args, **kwargs):
        pk = kwargs.get('client_pk')
        if (request.user.is_superuser or
                models.Client.objects.filter(
                    pk=pk,
                    auth_groups__user=request.user,
                ).exists()):
            return view(request, *args, **kwargs)
        else:
            return HttpResponseForbidden(
                'You do not have access to this area.'
            )

    if isinstance(view, type):
        view.dispatch = method_decorator(auth_client_required)(view.dispatch)
        return view
    else:
        return verify_client_auth_relation
