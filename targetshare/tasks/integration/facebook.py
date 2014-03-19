import logging

from celery import shared_task

from targetshare.models.dynamo import Token
from targetshare.integration import facebook


LOG = logging.getLogger(__name__)


@shared_task
def store_oauth_token(fb_app_id, code, redirect_uri):
    try:
        token_data = facebook.client.get_oauth_token(fb_app_id, code, redirect_uri)
    except (RuntimeError, IOError):
        LOG.exception("Failed to retrieve OAuth token")
        return

    token_value = token_data['access_token']
    token_expires = token_data['expires']

    try:
        debug_data = facebook.client.debug_token(fb_app_id, token_value)
    except (RuntimeError, IOError):
        LOG.exception("Failed to retrieve OAuth token debug data")
        return

    fbid = debug_data['data']['user_id']

    token = Token(
        fbid=fbid,
        appid=fb_app_id,
        token=token_value,
        expires=token_expires,
    )
    token.save(overwrite=True)
