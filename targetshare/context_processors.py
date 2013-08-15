from django.conf import settings


def context_settings(request):
    return {'settings': settings}
