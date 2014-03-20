import logging

from celery import shared_task

from targetshare.models.dynamo import Token
from targetshare.integration import facebook


LOG = logging.getLogger(__name__)


@shared_task(default_retry_delay=300, max_retries=5)
def store_oauth_token(fb_app_id, code, redirect_uri):
    try:
        token_data = facebook.client.get_oauth_token(fb_app_id, code, redirect_uri)
        token_value = token_data['access_token']
    except (KeyError, IOError, RuntimeError) as exc:
        LOG.warning("Failed to retrieve OAuth token", exc_info=True)
        store_oauth_token.retry(exc=exc)

    try:
        debug_data = facebook.client.debug_token(fb_app_id, token_value)

        if not debug_data['data']['is_valid']:
            LOG.error("OAuth token invalid")
            return

        token_fbid = debug_data['data']['user_id']
        token_expires = debug_data['data']['expires_at']
    except (KeyError, IOError) as exc:
        store_oauth_token.retry(exc=exc)

    token = Token(
        fbid=token_fbid,
        appid=fb_app_id,
        token=token_value,
        expires=token_expires,
    )
    token.save(overwrite=True)
