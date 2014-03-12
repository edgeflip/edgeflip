import django.conf

from jsurls.conf import settings


def jsurls(request):
    if django.conf.settings.DEBUG:
        jsurls_url = settings.DEBUG_URL
    else:
        jsurls_url = settings.STATIC_URL
    return {'JSURLS_URL': jsurls_url}
