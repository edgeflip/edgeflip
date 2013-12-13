import logging

from django import http
from django.shortcuts import render
from django.db.models import F
from django.views.decorators.http import require_POST

from targetshare import models
from targetshare.views import utils
from targetshare.integration import facebook
from targetshare.tasks import db

LOG = logging.getLogger(__name__)


@require_POST
@utils.require_visit
def record_event(request):
    """Endpoint to record user events (asynchronously)."""
    user_id = request.POST.get('userid')
    app_id = request.POST.get('appid')
    campaign_id = request.POST.get('campaignid')
    content_id = request.POST.get('contentid')
    content = request.POST.get('content')
    action_id = request.POST.get('actionid')
    event_type = request.POST.get('eventType')
    extend_token = request.POST.get('extend_token', False)
    friends = [int(fid) for fid in request.POST.getlist('friends[]')]

    single_occurrence_events = {'button_load', 'authorized'}
    multi_occurrence_events = {
        'button_click', 'auth_fail', 'select_all_click',
        'share_click', 'share_fail', 'shared', 'clickback',
        'suggest_message_click', 'selected_friend', 'unselected_friend',
        'faces_page_rendered', 'empty_share'
    }
    updateable_events = {'heartbeat'}

    if event_type not in single_occurrence_events | multi_occurrence_events | updateable_events:
        return http.HttpResponseForbidden(
            "Ah, ah, ah. You didn't say the magic word"
        )

    logged_events = request.session.setdefault('events', {})
    app_events = logged_events.setdefault(request.visit.app_id, set())
    if event_type in single_occurrence_events and event_type in app_events:
        # Already logged it
        return http.HttpResponse()

    events = []
    if friends and event_type not in updateable_events:
        for friend in friends:
            events.append(
                models.relational.Event(
                    visit=request.visit,
                    campaign_id=campaign_id,
                    client_content_id=content_id,
                    friend_fbid=friend,
                    content=content,
                    activity_id=action_id,
                    event_type=event_type,
                )
            )
    elif event_type in updateable_events:
        event, created = models.relational.Event.objects.get_or_create(
            visit=request.visit,
            campaign_id=campaign_id,
            client_content_id=content_id,
            activity_id=action_id,
            event_type=event_type,
            defaults={'content': 1}
        )
        if not created:
            # Maybe a count column on events would be useful? Hard to envision
            # many other events leveraging this
            event.content = F('content') + 1
            event.save()
    else:
        events.append(
            models.relational.Event(
                visit=request.visit,
                campaign_id=campaign_id,
                client_content_id=content_id,
                content=content,
                activity_id=action_id,
                event_type=event_type,
            )
        )

    if events:
        db.bulk_create.delay(events)

        if event_type in single_occurrence_events:
            # Prevent dupe logging
            app_events.add(event_type)
            request.session.modified = True

    if event_type == 'authorized':
        try:
            fbid = int(user_id)
            appid = int(app_id)
            token_string = request.POST['token']
        except (KeyError, ValueError, TypeError):
            msg = (
                "Cannot write authorization for fbid {!r}, appid {!r} and token {!r}"
                .format(user_id, app_id, request.POST.get('token'))
            )
            LOG.warning(msg, exc_info=True)
            return http.HttpResponseBadRequest(msg)

        try:
            client = models.Client.objects.get(campaigns__campaign_id=campaign_id)
        except models.Client.DoesNotExist:
            LOG.exception(
                "Failed to write authorization for fbid %r and token %r under "
                "campaign %r for non-existent client",
                fbid, token_string, campaign_id,
            )
            raise

        client.userclients.get_or_create(fbid=fbid)
        if extend_token:
            token = facebook.client.extend_token(fbid, appid, token_string)
            token.save(overwrite=True)

    if event_type == 'shared':
        # If this was a share, write these friends to the exclusions table so
        # we don't show them for the same content/campaign again
        exclusions = [
            {
                'fbid': user_id,
                'campaign_id': campaign_id,
                'content_id': content_id,
                'friend_fbid': friend,
                'defaults': {
                    'reason': 'shared',
                }
            } for friend in friends
        ]
        if exclusions:
            db.get_or_create.delay(models.relational.FaceExclusion, *exclusions)

    error_msg = request.POST.get('errorMsg[message]')
    if error_msg:
        # may want to push these to the DB at some point, but at least for now,
        # dump them to the logs to ensure we keep the data.
        LOG.error(
            'Front-end error encountered for user %s in session %s: %s',
            user_id, request.session.session_key, error_msg
        )

    share_msg = request.POST.get('shareMsg')
    if share_msg:
        db.delayed_save.delay(
            models.relational.ShareMessage(
                activity_id=action_id,
                fbid=user_id,
                campaign_id=campaign_id,
                content_id=content_id,
                message=share_msg,
            )
        )

    return http.HttpResponse()


@require_POST
@utils.require_visit
def suppress(request):
    user_id = request.POST.get('userid')
    campaign_id = request.POST.get('campaignid')
    content_id = request.POST.get('contentid')
    content = request.POST.get('content')
    old_id = request.POST.get('oldid')

    new_id = request.POST.get('newid')
    fname = request.POST.get('fname')
    lname = request.POST.get('lname')

    db.delayed_save.delay(
        models.relational.Event(
            visit=request.visit,
            campaign_id=campaign_id,
            client_content_id=content_id,
            friend_fbid=old_id,
            content=content,
            event_type='suppressed',
        )
    )
    db.delayed_save.delay(
        models.relational.FaceExclusion(
            fbid=user_id,
            campaign_id=campaign_id,
            content_id=content_id,
            friend_fbid=old_id,
            reason='suppressed',
        )
    )

    if new_id:
        db.delayed_save.delay(
            models.relational.Event(
                visit=request.visit,
                campaign_id=campaign_id,
                client_content_id=content_id,
                friend_fbid=new_id,
                content=content,
                event_type="shown",
            )
        )
        return render(request, 'targetshare/new_face.html', {
            'fbid': new_id,
            'firstname': fname,
            'lastname': lname,
        })
    else:
        return http.HttpResponse()
