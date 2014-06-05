import django.conf
from django import http
from django.core.exceptions import ImproperlyConfigured
from django.views.decorators.http import require_GET

from jsurls import compiler
from jsurls.conf import Profile, settings


@require_GET
def serve(request, profile=None, namespaces=(), includes=(), excludes=(), js_namespace=None):
    if not django.conf.settings.DEBUG:
        raise ImproperlyConfigured("The jsurls view can only be used in debug mode")

    if profile:
        if namespaces or includes or excludes or js_namespace:
            raise TypeError("profile_name argument incompatible with other arguments")

        try:
            profile = settings.PROFILES[profile]
        except KeyError:
            raise ValueError("no such profile: {}".format(profile))

    else:
        profile = Profile(settings,
                          URL_NAMESPACES=namespaces,
                          URL_INCLUDES=includes,
                          URL_EXCLUDES=excludes)
        if js_namespace:
            profile.JS_NAMESPACE = js_namespace

    paths = compiler.compile_lookup(
        namespaces=profile.URL_NAMESPACES,
        includes=profile.URL_INCLUDES,
        excludes=profile.URL_EXCLUDES,
    )
    javascript = compiler.render_js(paths, profile.JS_NAMESPACE)

    return http.HttpResponse(javascript, content_type='text/javascript')
