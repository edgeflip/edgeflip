import logging

from celery import shared_task
from django.db import transaction

from targetshare.models import relational
from targetshare.integration import facebook


LOG = logging.getLogger('crow')


@shared_task(default_retry_delay=300, max_retries=2)
def store_oauth_token(client_id, code, redirect_uri,
                      visit_id=None, campaign_id=None, content_id=None):
    client = relational.Client.objects.get(client_id=client_id)

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

    token = facebook.client.extend_token(token_fbid, client.fb_app_id, token_value, token_expires)
    token.save(overwrite=True)
    client.userclients.get_or_create(fbid=token.fbid)

    if visit_id:
        visit = relational.Visit.objects.get(visit_id=visit_id)

        # Ensure Visitor.fbid:
        visitor = visit.visitor
        if not visitor.fbid:
            visitor.fbid = token.fbid
            visitor.save(update_fields=['fbid'])
        elif visitor.fbid != token.fbid:
            LOG.warning("Visitor of Visit %s has mismatching FBID", visit.visit_id)
            (visitor, _created) = relational.Visitor.objects.get_or_create(fbid=token.fbid)
            visit.visitor = visitor
            visit.save(update_fields=['visitor'])

        # Record auth event (if e.g. faces hasn't already done it):
        with transaction.commit_on_success():
            relational.Event.objects.select_for_update().get_or_create(
                visit=visit,
                event_type='authorized',
                defaults={
                    'content': 'oauth',
                    'campaign_id': campaign_id,
                    'client_content_id': content_id,
                },
            )
