import json

from django import http


class JsonHttpResponse(http.HttpResponse):
    """HttpResponse which JSON-encodes its content and whose Content-Type defaults
    to "application/json".

    """
    def __init__(self, content=None, content_type='application/json', *args, **kws):
        super(JsonHttpResponse, self).__init__(
            content=json.dumps(content), content_type=content_type, *args, **kws)
