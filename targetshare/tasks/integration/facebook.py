import logging
import sys
import time

from celery import shared_task
from django.db import IntegrityError, transaction
from django.utils import six

from targetshare.models import datastructs, dynamo, relational
from targetshare.integration import facebook
from targetshare.tasks import db


LOG = logging.getLogger('crow')


@shared_task(default_retry_delay=300, max_retries=9, ignore_result=True)
def extend_token(fbid, appid, token_value):
    secret = relational.FBApp.objects.values_list('secret', flat=True).get(appid=appid)

    now = time.time()
    try:
        extension = facebook.client.extend_token(fbid, appid, secret, token_value)
        access_token = extension['access_token']
        expires_in = int(extension['expires'])
    except (KeyError, IOError, ValueError) as exc:
        LOG.warning("Failed to extend token", exc_info=True)
        extend_token.retry(exc=exc)

    LOG.debug("Extended access token %s expires in %s seconds", access_token, expires_in)

    token = dynamo.Token(
        fbid=fbid,
        appid=appid,
        token=access_token,
        expires=(now + expires_in),
    )
    token.save(overwrite=True)


@shared_task(ignore_result=True)
def record_auth(fbid, visit_id, campaign_id=None, content_id=None):
    visit = relational.Visit.objects.get(visit_id=visit_id)

    # Ensure Visitor.fbid:
    visitor = visit.visitor
    if visitor.fbid != fbid:
        if visitor.fbid:
            # Visitor-in-hand already set; get-or-create matching visitor
            LOG.warning("Visitor of Visit %s has mismatching FBID", visit.visit_id)
            (visitor, _created) = relational.Visitor.objects.get_or_create(fbid=fbid)
        else:
            # Get matching visitor or update visitor-in-hand
            try:
                # Check for pre-existing Visitor with this fbid:
                visitor = relational.Visitor.objects.get(fbid=fbid)
            except relational.Visitor.DoesNotExist:
                try:
                    # Update the visitor we have:
                    visitor.fbid = fbid
                    with transaction.atomic():
                        visitor.save(update_fields=['fbid'])
                except IntegrityError:
                    exc_info = sys.exc_info()
                    try:
                        # Check for race condition:
                        visitor = relational.Visitor.objects.get(fbid=fbid)
                    except relational.Visitor.DoesNotExist:
                        six.reraise(*exc_info)

        visit.visitor = visitor
        visit.save(update_fields=['visitor'])

    # Record auth event (if e.g. faces hasn't already done it):
    with transaction.atomic():
        relational.Event.objects.select_for_update().get_or_create(
            visit=visit,
            event_type='authorized',
            defaults={
                'content': 'oauth',
                'campaign_id': campaign_id,
                'client_content_id': content_id,
            },
        )


@shared_task(default_retry_delay=300, max_retries=2)
def store_oauth_token(client_id, code, redirect_uri,
                      visit_id=None, campaign_id=None, content_id=None):
    fb_app = relational.FBApp.objects.get(clients__client_id=client_id)

    try:
        token_data = facebook.client.get_oauth_token(fb_app.appid, fb_app.secret, code, redirect_uri)
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
        debug_data = facebook.client.debug_token(fb_app.appid, fb_app.secret, token_value)

        if not debug_data['data']['is_valid']:
            LOG.fatal("OAuth token invalid")
            return

        token_fbid = debug_data['data']['user_id']
    except (KeyError, IOError) as exc:
        LOG.fatal("Failed to retrieve OAuth token data & giving up", exc_info=True)
        return

    token = datastructs.ShortToken(
        fbid=token_fbid,
        appid=fb_app.appid,
        token=token_value,
    )

    extend_token.delay(*token)
    db.get_or_create.delay(relational.UserClient, client_id=client_id, fbid=token.fbid)

    if visit_id:
        record_auth.delay(token.fbid, visit_id, campaign_id, content_id)

    return token
