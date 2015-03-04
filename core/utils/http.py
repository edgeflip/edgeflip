import json

from django import http
from django.core.serializers.json import DjangoJSONEncoder


class JsonHttpResponse(http.HttpResponse):
    """HttpResponse which JSON-encodes its content and whose Content-Type defaults
    to "application/json".

    """
    encoder = None

    @classmethod
    def dumps(cls, content, **kws):
        kws.setdefault('cls', cls.encoder)
        return json.dumps(content, **kws)

    def __init__(self, content=None, content_type='application/json', *args, **kws):
        dumpwords = {}
        for key in ('cls', 'separators'):
            try:
                value = kws.pop(key)
            except KeyError:
                pass
            else:
                dumpwords[key] = value

        super(JsonHttpResponse, self).__init__(
            content=self.dumps(content, **dumpwords),
            content_type=content_type,
            *args, **kws
        )


class DjangoJsonHttpResponse(JsonHttpResponse):

    encoder = DjangoJSONEncoder
