from django.http import HttpResponse
import json 

# taken from https://docs.djangoproject.com/en/1.5/topics/db/sql/#executing-custom-sql-directly
def dictfetchall(cursor):
    "Returns all rows from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

def isoformat_row(row, keys=['time',]):
    row = dict(row)
    for key in keys:
        row[key] = row[key].isoformat() if row[key] else None
    return row

def run_safe_query(cursor, query, args):
    try:
        cursor.execute(query, args)
        return dictfetchall(cursor)
    finally:
        cursor.close()

class JsonResponse(HttpResponse):

    def __init__(self, content={}, content_type=None):
        if not content_type: 
            content_type = 'application/json'
        super(JsonResponse, self).__init__(json.dumps(content), content_type=content_type)

