import decimal
import json

from django import template
from django.utils.safestring import mark_safe


register = template.Library()


class FlexibleJSONEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            integral = int(obj)
            return integral if integral == obj else str(obj)

        return super(FlexibleJSONEncoder, self).default(obj)


@register.filter(name='json')
def to_json(data):
    return json.dumps(data, cls=FlexibleJSONEncoder)


@register.filter(name='safejson')
def to_safe_json(data):
    return mark_safe(to_json(data))
