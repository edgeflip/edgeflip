import base64
import binascii
import os
import string
import sys

from django.db import models
from django.utils.text import slugify

from core.db.models import BaseModel


MIN_SLUG = 8
MAX_SLUG = 12


def int2str(number, alphabet, length=sys.maxint):
    """Convert the given int to a str of the given length, from the given alphabet.

    For example:

        >>> int2str(665218483893421, string.letters, 10)
        'dILjbrCXM'

    The result is unpadded, and so length cannot be ensured.

    Note that this is no different from converting the given base-10 number to an
    arbitrary base, using an arbitrary alphabet.

    Base-10 to base-2:

        >>> int2str(2, '01')
        '01'
        >>> int2str(5, '01')
        '101'

    Base-10 to base-10 (the result is not reversed):

        >>> int2str(5, string.digits)
        '5'
        >>> int2str(10, string.digits)
        '01'

    """
    alpha_len = len(alphabet)
    count = 0
    output = ''

    while number and count < length:
        (number, remainder) = divmod(number, alpha_len)
        output += alphabet[remainder]
        count += 1

    return output


def make_slug(length=MAX_SLUG, alphabet=string.letters):
    """Return an arbitrary identifier of given length from the given alphabet.

    If alphabet is None, a URL-safe, base64-encoded encoded slug is returned.

    The result is unpadded, and so length cannot be ensured.

    """
    unique = os.urandom(length)

    if alphabet is None:
        return base64.urlsafe_b64encode(unique).rstrip('=')

    number = int(binascii.hexlify(unique), 16)
    return int2str(number, alphabet, length)


class ShortenedUrl(BaseModel):
    """A record for an arbitrary, short alias (slug) for an arbitrary URL.

    The `slug` defaults to the result of `make_slug`. Only `url` is required.

    """
    campaign = models.ForeignKey('targetshare.Campaign', null=True, related_name='shortenedurls')
    description = models.TextField(blank=True, default='')
    event_type = models.SlugField(default='generic_redirect')
    slug = models.SlugField(primary_key=True, default=make_slug)
    url = models.URLField(max_length=2048)

    class Meta(BaseModel.Meta):
        db_table = 'shortened_urls'

    @staticmethod
    def make_slug(prefix=''):
        """Generate an appropriate, random slug.

            >>> ShortenedUrl.make_slug()
            'vytxeTZskVKR'

        To prepend a recognizable, non-arbitrary value, specify `prefix`:

            >>> ShortenedUrl.make_slug('Good Food')
            'good-food-vytxeTZs'

        """
        prefix = prefix and slugify(unicode(prefix)) + '-'
        length = max(MIN_SLUG, MAX_SLUG - len(prefix))
        slug = make_slug(length)
        return prefix + slug

    def __unicode__(self):
        return u"{0.slug} => {0.url}".format(self)
