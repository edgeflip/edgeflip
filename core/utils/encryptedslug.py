"""Hide implementation details from URLs via reversible message cryptography."""
import urllib

from core.utils import crypto
from core.utils.version import make_version


API_DEFAULT = '1.0'


def make_slug(campaign, client_content):
    """Generate an encrypted path slug for the given Campaign and ClientContent.

    Arguments:

        * `campaign`: a Campaign
        * `client_content`: a ClientContent or ClientContent ID

    """
    parts = (campaign.client.fb_app.api,
             campaign.campaign_id,
             getattr(client_content, 'content_id', client_content))
    raw_slug = '/'.join(str(part) for part in parts)
    return crypto.encodeDES(raw_slug)


def clean_params(*params):
    count = len(params)
    if 2 <= count <= 3:
        (campaign_id, content_id) = (int(part) for part in params[-2:])
        version = make_version(params[0] if count == 3 else API_DEFAULT)
        return (version, campaign_id, content_id)
    raise TypeError("unexpected parameter count")


def get_params(slug):
    """Extract request parameters from an encrypted path slug.

    Returns the parameters:

        * FB App version (optional, defaulting to 1.0)
        * Campaign ID
        * ClientContent ID

    """
    unquoted = urllib.unquote(slug) # in case padding was included and quoted
    decoded = crypto.decodeDES(unquoted)
    params = decoded.split('/')
    try:
        return clean_params(*params)
    except TypeError:
        raise ValueError("Decryption of slug {!r} yielded unparsable result: {!r}"
                         .format(slug, decoded))
