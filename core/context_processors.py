from django.conf import settings

from core import utils


def context_settings(request):
    return {'settings': settings}


def test_mode(request):
    try:
        mode = utils.TestMode.from_request(request)
    except (KeyError, ValueError):
        mode = None
    return {'test_mode': mode}
