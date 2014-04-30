from django import template
from django.conf import settings
from django.core.urlresolvers import reverse

register = template.Library()


@register.simple_tag(name='shorturl', takes_context=True)
def short_url(context, obj, protocol=''):
    """Construct the absolute, shortened URL for the given ShortenedUrl object.

        {% shorturl short %}

    Optionally specify the protocol:

        {% shorturl short protocol='https:' %}

    """
    try:
        host = settings.CHAPO_REDIRECTOR_DOMAIN
    except AttributeError:
        request = context['request']
        host = request.get_host()

    path = reverse('chapo:main', args=(obj.slug,))

    return '{protocol}//{host}{path}'.format(protocol=protocol, host=host, path=path)
