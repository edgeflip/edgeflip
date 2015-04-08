import base64
import hashlib
import hmac
import json
import logging
import re

from django.http import HttpResponseForbidden

from targetshare.models.relational import FBApp

from core.utils import crypto, decorators


LOG = logging.getLogger(__name__)

FB_ORIGIN = r'^https?://apps\.facebook\.com$'


class fb_signed(decorators.ConfiguredViewDecorator):

    def __init__(self, view, origin=FB_ORIGIN, default_appid=None):
        super(fb_signed, self).__init__(view)
        self._origin = re.compile(origin, re.I)
        self._default_appid = default_appid

    def __call__(self, request, *args, **kws):
        if request.method == 'POST':
            try:
                (appid, data) = self._validate_signature(request)
            except UnauthorizedSignedRequest as exc:
                LOG.warning("%r", exc, exc_info=True)
                return HttpResponseForbidden("Forbidden")
        else:
            appid = request.GET.get('appid') or self._default_appid
            data = None

        kws.update(appid=appid, signed=data)
        return super(fb_signed, self).__call__(request, *args, **kws)

    def _validate_signature(self, request):
        origin = request.META.get('HTTP_ORIGIN', '')
        signed = request.POST.get('signed_request', '')
        if self._origin.search(origin):
            try:
                (_raw_signature, payload) = parts = str(signed).split('.')
                (signature, decoded_payload) = (
                    base64.urlsafe_b64decode(crypto.repad(part))
                    for part in parts
                )
            except ValueError:
                pass
            else:
                for (appid, secret) in FBApp.objects.values_list('appid', 'secret').iterator():
                    expected_signature = hmac.new(str(secret), payload, hashlib.sha256).digest()
                    if expected_signature == signature:
                        return (appid, json.loads(decoded_payload))

                raise NoMatchingAppSecret(origin, signed)

        raise UnauthorizedSignedRequest(origin, signed)


class UnauthorizedSignedRequest(Exception):
    pass


class NoMatchingAppSecret(UnauthorizedSignedRequest):
    pass
