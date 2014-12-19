import functools

from django import http
from django.conf import settings


class TestMode(object):

    @classmethod
    def from_request(cls, request):
        """Whether the request may be put into "test mode".

        Returns: a TestMode object.

        Raises: ValueError or KeyError if the correct "secret" is supplied but
        "fbid" or "token" is missing or invalid.

        """
        mode = request.GET.get('secret', '') == settings.TEST_MODE_SECRET
        fbid = request.GET.get('fbid', '')
        return cls(
            mode=mode,
            fbid=(int(fbid) if mode else None),
            token=(request.GET['token'] if mode else None),
        )

    def __init__(self, mode, fbid, token):
        self.mode = mode
        self.fbid = fbid
        self.token = token

    def __nonzero__(self):
        return self.mode
    __bool__ = __nonzero__


def test_mode(view):
    """View decorator injecting a TestMode object into its call keywords.

        @test_mode
        def myview(request, test_mode):
            ...

    Returns a Bad Request response if the correct "secret" is supplied but
    "fbid" or "token" is missing or invalid.

    """
    @functools.wraps(view)
    def wrapped(request, *args, **kws):
        try:
            kws['test_mode'] = TestMode.from_request(request)
        except (KeyError, ValueError):
            return http.HttpResponseBadRequest('Test mode requires numeric ID ("fbid") '
                                                'and Token ("token")')
        return view(request, *args, **kws)
    return wrapped


__test__ = False # go away nose
