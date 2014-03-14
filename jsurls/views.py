from itertools import chain

import django.conf
from django import http
from django.core.exceptions import ImproperlyConfigured
from django.views.decorators.http import require_GET

from jsurls import compiler
from jsurls.conf import settings


@require_GET
def serve(request, namespaces=(), includes=(), excludes=(), js_namespace=None):
    if not django.conf.settings.DEBUG:
        raise ImproperlyConfigured("The jsurls view can only be used in debug mode")

    if namespaces is not compiler.All:
        namespaces = tuple(chain(settings.URL_NAMESPACES, namespaces))

    paths = compiler.compile_lookup(
        namespaces=namespaces,
        includes=tuple(chain(settings.URL_INCLUDES, includes)),
        excludes=tuple(chain(settings.URL_EXCLUDES, excludes)),
    )
    javascript = compiler.render_js(paths, js_namespace or settings.JS_NAMESPACE)

    return http.HttpResponse(javascript, content_type='text/javascript')
