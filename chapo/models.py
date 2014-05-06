import base64
import binascii
import os
import string

from django.db import models
from django.utils.text import slugify

from core.models import base


MIN_SLUG = 8
MAX_SLUG = 12


def number_to_string(number, length, alphabet):
    """Convert the given number to a string of the given length, from the given alphabet.

    For example:

        >>> number_to_string(665218483893421, 10, string.letters)
        'dILjbrCXM'

    The result is unpadded, and so length cannot be ensured.

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
    return number_to_string(number, length, alphabet)


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
    def make_slug(prefix=''):
        """Generate an appropriate, unique slug.

            >>> ShortenedUrl.make_slug()
            'vytxeTZskVKR'

        To prepend a recognizable, non-arbitrary value, specify `prefix`:

            >>> ShortenedUrl.make_slug('Good Food')
            'good-food-vytxeTZskVKR'

        """
        prefix = prefix and slugify(unicode(prefix)) + '-'
        length = max(MIN_SLUG, MAX_SLUG - len(prefix))
        slug = make_slug(length)
        return prefix + slug

    def __unicode__(self):
        return u"{0.slug} => {0.url}".format(self)
