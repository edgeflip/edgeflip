import re


EMBEDDED_NS_PATTERN = re.compile(r'\bcanvas\b')
EMBEDDED_PATH_TOKEN = '/canvas/'


def get_embedded_path(fb_app, path):
    (_base_path, rel_path) = path.rsplit(EMBEDDED_PATH_TOKEN, 1)
    return 'https://apps.facebook.com/{}/{}'.format(fb_app.name, rel_path)


class AccessSignature(object):

    __slots__ = ('code', 'redirect_uri', 'redirect_query')

    def __init__(self, code=None, redirect_uri=None, redirect_query=None):
        self.code = code
        self.redirect_uri = redirect_uri
        self.redirect_query = redirect_query

    def is_valid(self):
        for slot in ('code', 'redirect_uri'):
            if not getattr(self, slot, None):
                return False
        return True


class AccessDenied(Exception):
    pass


def handle_incoming(request, fb_app):
    (error, error_reason) = (request.GET.get('error'),
                             request.GET.get('error_reason'))
    if error == 'access_denied' and error_reason == 'user_denied':
        raise AccessDenied(error_reason)

    # Remove FB junk from query:
    redirect_query = request.GET.copy()
    for key in ('code', 'error', 'error_reason', 'error_description'):
        try:
            del redirect_query[key]
        except KeyError:
            pass

    code = request.GET.get('code')
    if code:
        # OAuth permission

        # Rebuild OAuth redirect uri from request, (without FB junk):
        if redirect_query:
            redirect_path = "{}?{}".format(request.path, redirect_query)
        else:
            redirect_path = request.path

        namespace = request.resolver_match.namespace
        if namespace and EMBEDDED_NS_PATTERN.search(namespace):
            redirect_uri = get_embedded_path(fb_app, redirect_path)
        else:
            redirect_uri = request.build_absolute_uri(redirect_path)

        return AccessSignature(code, redirect_uri, redirect_query)

    return AccessSignature(code, None, redirect_query)
