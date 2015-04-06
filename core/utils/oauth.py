class AccessSignature(object):

    __slots__ = ('code', 'redirect_uri', 'redirect_query')

    def __init__(self, code=None, redirect_uri=None, redirect_query=None):
        self.code = code
        self.redirect_uri = redirect_uri
        self.redirect_query = redirect_query

    def is_valid(self):
        for slot in self.__slots__:
            if not getattr(self, slot, None):
                return False
        return True


class AccessDenied(Exception):
    pass


def handle_incoming(request):
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

        return AccessSignature(code, request.build_absolute_uri(redirect_path), redirect_query)

    return AccessSignature(code, None, redirect_query)
