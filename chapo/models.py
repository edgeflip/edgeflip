from uuid import uuid4
from base64 import urlsafe_b64encode

from django.db import models
from django.utils.text import slugify

from core.models import base


def make_slug():
    """Return a URL-safe, base64-encoded, universally-unique identifier.

    Padding is stripped (and so length cannot be ensured).

    """
    return urlsafe_b64encode(uuid4().bytes).rstrip('=')


class ShortenedUrl(base.BaseModel):
    """A record for an arbitrary, short alias (slug) for an arbitrary URL.

    The `slug` defaults to the result of `make_slug`. Only `url` is required.

    """
    campaign = models.ForeignKey('targetshare.Campaign', null=True)
    description = models.TextField(blank=True, default='')
    event_type = models.SlugField(default='generic_redirect')
    slug = models.SlugField(primary_key=True, default=make_slug)
    url = models.URLField(max_length=2048)

    class Meta(base.BaseModel.Meta):
        db_table = 'shortened_urls'

    @staticmethod
    def make_slug(prepend=None):
        """Generate an appropriate, unique slug.

            >>> ShortenedUrl.make_slug()
            'vytxeTZskVKR'

        To prepend a recognizable, non-arbitrary value, specify `prepend`:

            >>> ShortenedUrl.make_slug('Good Food')
            'good-food-vytxeTZskVKR'

        """
        slug = make_slug()

        if prepend:
            return '{}-{}'.format(slugify(unicode(prepend)), slug)

        return slug

    def __unicode__(self):
        return u"{0.slug} => {0.url}".format(self)
