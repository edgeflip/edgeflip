from django.http import HttpResponse
import json 

def isoformat_row(row, keys=['time',]):
    row = dict(row)
    for key in keys:
        row[key] = row[key].isoformat() if row[key] else None
    return row

class JsonResponse(HttpResponse):

    def __init__(self, content={}, content_type=None):
        if not content_type: 
            content_type = 'application/json'
        super(JsonResponse, self).__init__(json.dumps(content), content_type=content_type)

