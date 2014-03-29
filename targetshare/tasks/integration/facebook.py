import logging

from celery import shared_task

from targetshare.models.dynamo import Token
from targetshare.models.relational import Client
from targetshare.integration import facebook


LOG = logging.getLogger('crow')


@shared_task(default_retry_delay=300, max_retries=2)
def store_oauth_token(client_id, code, redirect_uri):
    client = Client.objects.get(client_id=client_id)

    try:
        token_data = facebook.client.get_oauth_token(client.fb_app_id, code, redirect_uri)
        token_value = token_data['access_token']
    except (KeyError, IOError, RuntimeError) as exc:
        # IOError should cover all networking errors, but depending on the
        # version of requests lib, it'll descend from RuntimeError
        content = ''
        status_code = None
        if hasattr(exc, 'response'):
            content = getattr(exc.response, 'content', content)
            status_code = getattr(exc.response, 'status_code', status_code)

        content = content and ": {}".format(content)

        if status_code == 400:
            LOG.fatal("Failed to retrieve OAuth token & giving up%s", content, exc_info=True)
            return
        else:
            LOG.warning("Failed to retrieve OAuth token%s", content, exc_info=True)
            store_oauth_token.retry(exc=exc)

    try:
        debug_data = facebook.client.debug_token(client.fb_app_id, token_value)

        if not debug_data['data']['is_valid']:
            LOG.fatal("OAuth token invalid")
            return

        token_fbid = debug_data['data']['user_id']
        token_expires = debug_data['data']['expires_at']
    except (KeyError, IOError) as exc:
        LOG.warning("Failed to retrieve OAuth token data", exc_info=True)
        store_oauth_token.retry(exc=exc)

    token = Token(
        fbid=token_fbid,
        appid=client.fb_app_id,
        token=token_value,
        expires=token_expires,
    )
    token.save(overwrite=True)
    client.userclients.get_or_create(fbid=token.fbid)
