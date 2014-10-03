from django.core import cache
from django.http import HttpResponse
import json

# taken from https://docs.djangoproject.com/en/1.5/topics/db/sql/#executing-custom-sql-directly
def dictfetchall(cursor):
    "Returns all rows from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

def isoformat_dict(dictionary, keys=['time',]):
    for key in keys:
        dictionary[key] = dictionary[key].isoformat() if dictionary[key] else None
    return dictionary


def isoformat_row(row, indices):
    for index in indices:
        row[index] = row[index].isoformat()
    return row


def run_safe_dict_query(cursor, query, args):
    try:
        cursor.execute(query, args)
        return dictfetchall(cursor)
    finally:
        cursor.close()

def run_safe_row_query(cursor, query, args):
    try:
        cursor.execute(query, args)
        return [list(row) for row in cursor.fetchall()]
    finally:
        cursor.close()

class JsonResponse(HttpResponse):

    def __init__(self, content=None, content_type=None):
        if not content_type:
            content_type = 'application/json'
        super(JsonResponse, self).__init__(json.dumps(content), content_type=content_type)


def cached_value(prefix, identifier, value_generator):
    cache_key = '|'.join(['reporting', prefix, str(identifier)])
    data = cache.cache.get(cache_key)
    if not data:
        data = value_generator()
        cache.cache.set(cache_key, data)
    return data
