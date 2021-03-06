import logging

from django import http
from django.db import transaction
from django.db.models import F
from django.shortcuts import render
from django.views.decorators.http import require_POST

from targetshare.models import relational
from targetshare.tasks import db
from targetshare.tasks.integration.facebook import extend_token
from targetshare.views import PENDING_EXCLUSIONS_KEY, utils

LOG = logging.getLogger('crow')

SINGULAR_EVENTS = {'button_load', 'authorized'}
UPDATED_EVENTS = {'heartbeat'}
REPEATED_EVENTS = {
    'button_click',
    'auth_fail',
    'select_all_click',
    'share_click',
    'share_fail',
    'shared',
    'clickback',
    'suggest_message_click',
    'selected_friend',
    'unselected_friend',
    'manually_selected_friend',
    'manually_unselected_friend',
    'faces_page_rendered',
    'empty_share',
    'publish_declined',
    'publish_accepted',
    'publish_reminder_accepted',
    'publish_reminder_declined',
    'publish_unknown',
}
ALL_EVENTS = SINGULAR_EVENTS | REPEATED_EVENTS | UPDATED_EVENTS


@require_POST
@utils.require_visit
def record_event(request):
    """Endpoint to record user events."""
    user_id = request.POST.get('userid')
    app_id = request.POST.get('appid')
    campaign_id = request.POST.get('campaignid')
    content_id = request.POST.get('contentid')
    content = request.POST.get('content', '')
    action_id = request.POST.get('actionid')
    event_type = request.POST.get('eventType')
    extend = request.POST.get('extend_token', False)

    (friends, friend_fbids) = ([], [])
    for uid in request.POST.getlist('friends[]'):
        if uid.isdigit():
            uid = int(uid)
            friend_fbids.append(uid)
        friends.append(uid)

    if campaign_id:
        try:
            campaign = relational.Campaign.objects.get(campaign_id=campaign_id)
        except (relational.Campaign.DoesNotExist, ValueError):
            return http.HttpResponseBadRequest("No such campaign: {}".format(campaign_id))
    else:
        campaign = None

    if event_type not in ALL_EVENTS:
        return http.HttpResponseForbidden("Ah, ah, ah. You didn't say the magic word")

    # Create event(s) according to record type #

    if event_type in SINGULAR_EVENTS:
        request.visit.events.first_or_create(
            event_type=event_type,
            defaults={
                'campaign_id': campaign_id,
                'client_content_id': content_id,
                'content': content,
                'activity_id': action_id,
            }
        )
    elif event_type in UPDATED_EVENTS:
        # This is (currently) just the 'heartbeat' event
        with transaction.atomic():
            (event, created) = relational.Event.objects.select_for_update().first_or_create(
                event_type=event_type,
                visit=request.visit,
                defaults={
                    'campaign_id': campaign_id,
                    'client_content_id': content_id,
                    'content': '1',
                }
            )
            if not created:
                if campaign_id and not event.campaign_id:
                    event.campaign_id = campaign_id
                if content_id and not event.client_content_id:
                    event.client_content_id = content_id
                event.content = F('content') + 1
                event.save()
    elif friends:
        db.bulk_create.delay([
            relational.Event(
                visit_id=request.visit.visit_id,
                campaign_id=campaign_id,
                client_content_id=content_id,
                friend_fbid=friend if isinstance(friend, int) else None,
                content=content,
                activity_id=action_id,
                event_type=event_type,
            )
            for friend in friends
        ])
    else:
        db.delayed_save.delay(
            relational.Event(
                visit_id=request.visit.visit_id,
                campaign_id=campaign_id,
                client_content_id=content_id,
                content=content[:1028],
                activity_id=action_id,
                event_type=event_type,
            )
        )

    # Additional, event_type-specific handling #

    if event_type == 'authorized':
        try:
            fbid = int(user_id)
            appid = int(app_id)
            token_string = request.POST['token']
            api = request.POST['api']
        except (KeyError, ValueError, TypeError):
            fbid = appid = token_string = api = None

        if not all([fbid, appid, token_string, campaign, api]):
            msg = ("Cannot write authorization for fbid %r, appid %r, api %r "
                   "and token %r under campaign %r")
            args = (user_id, app_id, request.POST.get('api'),
                    request.POST.get('token'), campaign_id)
            LOG.warning(msg, *args, extra={'request': request})
            return http.HttpResponseBadRequest(msg % args)

        campaign.client.userclients.get_or_create(fbid=fbid)
        if extend:
            extend_token.delay(fbid, appid, token_string, api)

    elif event_type == 'shared':
        root_campaign = relational.Campaign.objects.get(rootcampaign_properties__campaign=campaign_id)

        # Write friends with whom we shared to the exclusions table,
        # so we don't show them for the same content/campaign again.
        # Rather than wait on as many as 10 get+inserts, background the task.
        exclusions = [
            {
                'fbid': user_id,
                'campaign_id': root_campaign.campaign_id,
                'content_id': content_id,
                'friend_fbid': friend,
                'defaults': {
                    'reason': 'shared',
                }
            } for friend in friend_fbids
        ]
        if exclusions:
            db.get_or_create.delay(relational.FaceExclusion, *exclusions)

        # Attempt to avoid race condition between subsequent reload of faces
        # page and above record of exclusions by storing these in session:
        faces_exclusions_key = PENDING_EXCLUSIONS_KEY.format(campaign_id=root_campaign.campaign_id,
                                                             content_id=content_id,
                                                             fbid=user_id)
        request.session[faces_exclusions_key] = friend_fbids

    # Additional handling #

    error_msg = request.POST.get('errorMsg[message]')
    if error_msg:
        # may want to push these to the DB at some point, but at least for now,
        # dump them to the logs to ensure we keep the data.
        LOG.warning(
            'Front-end error encountered for user %s in session %s: %s',
            user_id, request.session.session_key, error_msg,
            extra={'request': request}
        )

    share_msg = request.POST.get('shareMsg')
    if share_msg:
        db.delayed_save.delay(
            relational.ShareMessage(
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
    old_id = request.POST.get('oldid', '')

    new_id = request.POST.get('newid')
    fname = request.POST.get('fname', '')
    lname = request.POST.get('lname', '')
    picture = request.POST.get('pic')

    root_campaign = relational.Campaign.objects.get(rootcampaign_properties__campaign=campaign_id)

    request.visit.events.create(
        campaign_id=campaign_id,
        client_content_id=content_id,
        friend_fbid=old_id if old_id.isdigit() else None,
        event_type='suppressed',
    )
    if old_id.isdigit():
        root_campaign.faceexclusion_set.get_or_create(
            fbid=user_id,
            content_id=content_id,
            friend_fbid=old_id,
            defaults={'reason': 'suppressed'},
        )

    if new_id:
        request.visit.events.create(
            campaign_id=campaign_id,
            client_content_id=content_id,
            friend_fbid=new_id if new_id.isdigit() else None,
            content=u"{} {}".format(fname, lname),
            event_type='shown',
        )
        return render(request, 'targetshare/new_face.html', {
            'uid': new_id,
            'firstname': fname,
            'lastname': lname,
            'picture': picture,
        })

    return http.HttpResponse()
