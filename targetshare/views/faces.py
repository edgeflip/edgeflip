import logging
import urllib
import itertools

import celery
from django import http
from django.core.serializers import serialize
from django.core.urlresolvers import reverse
from django.shortcuts import render, get_object_or_404
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from faraday.structs import LazyList

from targetshare import forms
from targetshare.integration import facebook
from targetshare.models import datastructs, dynamo, relational
from targetshare.tasks import db, targeting
from targetshare.tasks.integration.facebook import extend_token
from targetshare.views import FACES_TASKS_KEY, OAUTH_TASK_KEY, PENDING_EXCLUSIONS_KEY, utils


LOG = logging.getLogger('crow')

MAX_FACES = 50


def request_targeting(visit, token, campaign, client_content, num_faces):
    """Kick off targeting tasks and record event."""
    task_px3 = targeting.proximity_rank_three.delay(
        token=token,
        visit_id=visit.pk,
        campaign_id=campaign.pk,
        content_id=client_content.pk,
        num_faces=num_faces,
    )
    task_px4 = targeting.proximity_rank_four.delay(
        token=token,
        visit_id=visit.pk,
        campaign_id=campaign.pk,
        content_id=client_content.pk,
        num_faces=num_faces,
        px3_task_id=task_px3.id,
    )
    visit.events.create(
        event_type='targeting_requested',
        campaign_id=campaign.pk,
        client_content_id=client_content.pk,
        content="px3_task_id: {}, px4_task_id: {}".format(task_px3.id, task_px4.id),
    )
    return (task_px3, task_px4)


@csrf_exempt # FB posts directly to this view
@utils.encoded_endpoint
@utils.require_visit
def frame_faces(request, campaign_id, content_id, canvas=False):
    campaign = get_object_or_404(relational.Campaign, campaign_id=campaign_id)
    campaign_properties = campaign.campaignproperties.get()
    if campaign_properties.root_campaign_id != campaign_properties.campaign_id:
        LOG.warning("Received request for non-root campaign", extra={'request': request})
        raise http.Http404

    client = campaign.client
    content = get_object_or_404(client.clientcontent, content_id=content_id)

    db.bulk_create.delay([
        relational.Event(
            visit_id=request.visit.pk,
            campaign_id=campaign.pk,
            client_content_id=content.pk,
            event_type='faces_page_load',
        ),
        relational.Event(
            visit_id=request.visit.pk,
            campaign_id=campaign.pk,
            client_content_id=content.pk,
            event_type=('faces_canvas_load' if canvas else 'faces_iframe_load'),
        )
    ])

    # If the visitor passed through FB OAuth and our incoming redirector, we
    # may be able to retrieve the result of their store_oauth_token job,
    # determine their FBID & token, and eagerly start their targeting jobs.
    task_id_oauth = request.session.get(OAUTH_TASK_KEY)
    if task_id_oauth:
        task_oauth = celery.current_app.AsyncResult(task_id_oauth)
        if task_oauth.ready():
            del request.session[OAUTH_TASK_KEY] # no need to do this again
            token = task_oauth.result if task_oauth.successful() else None
            if token:
                faces_tasks_key = FACES_TASKS_KEY.format(campaign_id=campaign_id,
                                                         content_id=content_id,
                                                         fbid=token.fbid)
                if faces_tasks_key not in request.session:
                    # Initiate targeting tasks:
                    (task_px3, task_px4) = request_targeting(
                        visit=request.visit,
                        token=token,
                        campaign=campaign,
                        client_content=content,
                        num_faces=campaign_properties.num_faces,
                    )
                    request.session[faces_tasks_key] = (task_px3.id, task_px4.id)

    page_styles = utils.assign_page_styles(
        request.visit,
        relational.Page.FRAME_FACES,
        campaign,
        content,
    )

    (serialized_properties,) = serialize('python', (campaign_properties,))
    properties = serialized_properties['fields']
    for override_key, field in [
        ('efsuccessurl', 'client_thanks_url'),
        ('eferrorurl', 'client_error_url'),
    ]:
        value = request.REQUEST.get(override_key) or properties[field]
        properties[field] = "{}?{}".format(
            reverse('outgoing', args=[client.fb_app_id, value]),
            urllib.urlencode({'campaignid': campaign_id}),
        )

    return render(request, 'targetshare/frame_faces.html', {
        'fb_params': {
            'fb_app_name': client.fb_app_name,
            'fb_app_id': client.fb_app_id,
        },
        'campaign': campaign,
        'content': content,
        'properties': properties,
        'campaign_css': page_styles,
        'canvas': canvas,
        # Debug mode currently on for all methods of targeted sharing
        # However will likely just reflect the canvas var in the future
        'debug_mode': True,
    })


@require_POST
@csrf_exempt
@utils.require_visit
def faces(request):
    faces_form = forms.FacesForm(request.POST)
    if not faces_form.is_valid():
        return utils.JsonHttpResponse(faces_form.errors, status=400)

    data = faces_form.cleaned_data
    campaign = root_campaign = data['campaign']
    content = data['content']
    client = campaign.client

    if not request.session.get('sessionverified', False):
        # Avoid spamming the workers with an agent who can't hold onto its session
        if data['last_call']:
            LOG.fatal("User agent failed cookie test. (Will return error to user.)",
                      extra={'request': request})
            return http.HttpResponseForbidden("Cookies are required.")

        # Agent failed test, but give it another shot
        LOG.warning("Suspicious session missing cookie test", extra={'request': request})
        request.session.set_test_cookie()
        return utils.JsonHttpResponse({
            'status': 'waiting',
            'reason': "Cookies are required. Please try again.",
            'campaignid': campaign.pk,
            'contentid': content.pk,
        }, status=202)

    faces_tasks_key = FACES_TASKS_KEY.format(campaign_id=campaign.pk,
                                             content_id=content.pk,
                                             fbid=data['fbid'])
    (task_id_px3, task_id_px4) = request.session.get(faces_tasks_key, (None, None))

    if task_id_px3 and task_id_px4:
        # Retrieve statuses of active targeting tasks #
        task_px3 = celery.current_app.AsyncResult(task_id_px3)
        task_px4 = celery.current_app.AsyncResult(task_id_px4)
    else:
        # First request #
        token = datastructs.ShortToken(
            fbid=data['fbid'],
            appid=client.fb_app_id,
            token=data['token'],
        )

        # Extend & store Token and record authorized UserClient:
        extend_token.delay(*token)
        db.get_or_create.delay(
            relational.UserClient,
            client_id=client.pk,
            fbid=data['fbid'],
        )

        # Initiate targeting tasks:
        (task_px3, task_px4) = request_targeting(
            visit=request.visit,
            token=token,
            campaign=campaign,
            client_content=content,
            num_faces=data['num_face'],
        )
        request.session[faces_tasks_key] = (task_px3.id, task_px4.id)

    # Check status #
    if not (task_px3.ready() and task_px4.ready()) and not task_px3.failed() and not data['last_call']:
        return utils.JsonHttpResponse({
            'status': 'waiting',
            'reason': "Identifying friends.",
            'campaignid': campaign.pk,
            'contentid': content.pk,
        }, status=202)

    # Select results #
    (result_px3, result_px4) = (
        task.result if task.successful() else targeting.empty_filtering_result
        for task in (task_px3, task_px4)
    )
    if result_px4.filtered is None:
        # px4 filtering didn't happen, so use px3
        if result_px4.ranked is None or result_px3.filtered is None:
            # either: px4 ranking didn't happen, as well;
            # or, it did, but we have no px3 filtering result to rerank,
            # (in which case we can error out later):
            targeting_result = result_px3
        else:
            # Re-rank px3 edges by px4 ranking:
            targeting_result = result_px3._replace(
                ranked=result_px4.ranked,
                filtered=result_px3.filtered.reranked(result_px4.ranked),
            )
    elif result_px3.ranked:
        targeting_result = result_px4._replace(
            filtered=result_px4.filtered.rescored(result_px3.ranked),
        )
    else:
        # px4 filtering completed, so use it:
        targeting_result = result_px4

    if not targeting_result.ranked or not targeting_result.filtered:
        if task_px3.ready():
            return http.HttpResponseServerError('No friends were identified for you.')
        else:
            LOG.fatal("px3 failed to complete in the time allotted (%s)",
                      task_px3.task_id, extra={'request': request})
            return http.HttpResponse('Response has taken too long, giving up', status=503)

    if targeting_result.campaign_id and targeting_result.campaign_id != campaign.pk:
        campaign = relational.Campaign.objects.get(pk=targeting_result.campaign_id)
    if targeting_result.content_id and targeting_result.content_id != content.pk:
        content = relational.ClientContent.objects.get(pk=targeting_result.content_id)

    # Apply campaign
    if data['efobjsrc']:
        fb_object = facebook.third_party.source_campaign_fbobject(campaign, data['efobjsrc'])
        db.delayed_save.delay(
            relational.Assignment.make_managed(
                visit_id=request.visit.pk,
                campaign_id=campaign.pk,
                content_id=content.pk,
                feature_row=fb_object,
                chosen_from_rows=None,
                manager=campaign.campaignfbobjects,
                random_assign=False,
            )
        )
    else:
        fb_object = campaign.campaignfbobjects.for_datetime().random_assign()
        db.delayed_save.delay(
            relational.Assignment.make_managed(
                visit_id=request.visit.pk,
                campaign_id=campaign.pk,
                content_id=content.pk,
                feature_row=fb_object,
                chosen_from_rows=campaign.campaignfbobjects.for_datetime(),
            )
        )

    fb_attrs = fb_object.fbobjectattribute_set.for_datetime().get()
    fb_object_url = 'https://%s%s?%s' % (
        request.get_host(),
        reverse('objects', kwargs={
            'fb_object_id': fb_object.pk,
            'content_id': content.pk,
        }),
        urllib.urlencode({
            'cssslug': targeting_result.choice_set_slug,
            'campaign_id': campaign.pk,
        }),
    )
    fb_params = {
        'fb_action_type': fb_attrs.og_action,
        'fb_object_type': fb_attrs.og_type,
        'fb_object_url': fb_object_url,
        'fb_app_name': client.fb_app_name,
        'fb_app_id': client.fb_app_id,
        'fb_object_title': fb_attrs.og_title,
        'fb_object_image': fb_attrs.og_image,
        'fb_object_description': fb_attrs.og_description
    }

    # Record generation of suggestions (but only once per set of tasks):
    num_gen = MAX_FACES
    generated = []
    for tier in targeting_result.filtered:
        edges_list = tier['edges'][:num_gen]
        tier_campaign_id = tier['campaign_id']
        tier_content_id = tier['content_id']
        for edge in edges_list:
            scores = (('N/A' if score is None else score)
                      for score in (edge.px3_score, edge.px4_score))
            generated.append({
                'visit_id': request.visit.visit_id,
                'campaign_id': tier_campaign_id,
                'client_content_id': tier_content_id,
                'friend_fbid': edge.secondary.fbid,
                'event_type': 'generated',
                'content': "px3_score: {0} ({px3_id}), px4_score: {1} ({px4_id})"
                           .format(*scores, px3_id=task_px3.id, px4_id=task_px4.id),
                'defaults': {
                    'event_datetime': timezone.now(),
                },
            })

        num_gen -= len(edges_list)
        if num_gen <= 0:
            break

    db.get_or_create.delay(relational.Event, *generated)

    # Re-apply exclusions to pick up any shares and suppressions since results first generated:
    faces_exclusions_key = PENDING_EXCLUSIONS_KEY.format(campaign_id=root_campaign.pk,
                                                         content_id=content.pk,
                                                         fbid=data['fbid'])
    enqueued_exclusions = request.session.get(faces_exclusions_key, ())
    existing_exclusions = root_campaign.faceexclusion_set.filter(
        fbid=data['fbid'],
        content=content,
    ).values_list('friend_fbid', flat=True)
    all_exclusions = set(itertools.chain(enqueued_exclusions, existing_exclusions.iterator()))

    # Determine faces that can be shown (and record these):
    (face_friends, show_faces, shown) = ([], [], [])
    eligible_edges = (edge for edge in targeting_result.filtered.iteredges()
                      if edge.secondary.fbid not in all_exclusions)
    for (edge_index, edge) in enumerate(itertools.islice(eligible_edges, MAX_FACES)):
        face_friends.append(edge.secondary)

        if edge_index < data['num_face']:
            show_faces.append(edge.secondary)

            if edge.px4_score is None:
                shown_content = "px3_score: {} ({})".format(edge.px3_score, task_px3.id)
            else:
                shown_content = "px4_score: {} ({})".format(edge.px4_score, task_px4.id)

            shown.append(
                relational.Event(
                    visit_id=request.visit.visit_id,
                    campaign_id=campaign.campaign_id,
                    client_content_id=content.content_id,
                    friend_fbid=edge.secondary.fbid,
                    content=shown_content,
                    event_type='shown',
                )
            )

    if not show_faces:
        LOG.fatal("No faces to show, (all suppressed). (Will return error to user.)",
                  extra={'request': request})
        return http.HttpResponseServerError("No friends remaining.")

    db.bulk_create.delay(shown)

    rendered_table = render_to_string('targetshare/faces_table.html', {
        'msg_params': {
            'sharing_prompt': fb_attrs.sharing_prompt,
            'sharing_sub_header': fb_attrs.sharing_sub_header,
            'sharing_button': fb_attrs.sharing_button,
            'msg1_pre': fb_attrs.msg1_pre,
            'msg1_post': fb_attrs.msg1_post,
            'msg2_pre': fb_attrs.msg2_pre,
            'msg2_post': fb_attrs.msg2_post,
        },
        'fb_params': fb_params,
        'all_friends': [edge.secondary for edge in targeting_result.ranked],
        'face_friends': face_friends,
        'show_faces': show_faces,
        'num_face': data['num_face'],
    }, context_instance=RequestContext(request))

    return utils.JsonHttpResponse({
        'status': 'success',
        'campaignid': campaign.pk,
        'contentid': content.pk,
        'html': rendered_table,
    })


def faces_email_friends(request, notification_uuid):
    ''' A view that's fairly similar to our Faces/Frame Faces views, except
    that this will not perform any crawls. We've already done the crawling
    in the background, so we can skip that here, and instead leverage the
    friends passed in via GET params.
    '''
    # Campaign setup
    notification_user = get_object_or_404(
        relational.NotificationUser,
        uuid=notification_uuid
    )
    campaign = notification_user.notification.campaign
    content = notification_user.notification.client_content
    client = campaign.client
    utils.set_visit(request, client.fb_app_id, notification_user.fbid, {
        'campaign': campaign,
        'client_content': content,
    })

    # Gather friend data
    user = dynamo.User.items.get_item(fbid=notification_user.fbid)
    friend_fbids = notification_user.events.filter(
        event_type__in=('generated', 'shown')
    ).values_list('friend_fbid', flat=True).distinct()
    face_friends = all_friends = dynamo.User.items.batch_get(
        keys=LazyList({'fbid': fbid} for fbid in friend_fbids)
    )
    shown_fbids = set(
        notification_user.events.filter(
            event_type='shown',
        ).values_list('friend_fbid', flat=True)
    )
    num_face = len(shown_fbids)
    show_faces = LazyList(friend for friend in face_friends
                          if friend.fbid in shown_fbids)

    db.delayed_save.delay(
        relational.Event(
            visit_id=request.visit.pk,
            campaign_id=campaign.pk,
            client_content_id=content.pk,
            event_type='faces_email_page_load',
        )
    )

    # FBObj setup
    fb_object = campaign.campaignfbobjects.for_datetime().random_assign()
    db.delayed_save.delay(
        relational.Assignment.make_managed(
            visit_id=request.visit.pk,
            campaign_id=campaign.pk,
            content_id=content.pk,
            feature_row=fb_object,
            chosen_from_rows=campaign.campaignfbobjects.for_datetime(),
        )
    )
    fb_attrs = fb_object.fbobjectattribute_set.get()
    fb_object_url = 'https://%s%s?%s' % (
        request.get_host(),
        reverse('objects', kwargs={
            'fb_object_id': fb_object.pk,
            'content_id': content.pk,
        }),
        urllib.urlencode({
            'campaign_id': campaign.pk,
        }),
    )

    fb_params = {
        'fb_action_type': fb_attrs.og_action,
        'fb_object_type': fb_attrs.og_type,
        'fb_object_url': fb_object_url,
        'fb_app_name': client.fb_app_name,
        'fb_app_id': client.fb_app_id,
        'fb_object_title': fb_attrs.og_title,
        'fb_object_image': fb_attrs.og_image,
        'fb_object_description': fb_attrs.og_description
    }
    msg_params = {
        'sharing_prompt': fb_attrs.sharing_prompt,
        'msg1_pre': fb_attrs.msg1_pre,
        'msg1_post': fb_attrs.msg1_post,
        'msg2_pre': fb_attrs.msg2_pre,
        'msg2_post': fb_attrs.msg2_post,
    }
    content_str = '%s:%s %s' % (
        fb_params['fb_app_name'],
        fb_params['fb_object_type'],
        fb_params['fb_object_url']
    )
    db.bulk_create.delay([
        relational.Event(
            visit_id=request.visit.pk,
            campaign_id=event.campaign.pk,
            client_content_id=event.client_content.pk,
            friend_fbid=event.friend_fbid,
            content=content_str,
            event_type=event.event_type,
        )
        for event in notification_user.events.iterator()
    ])
    db.bulk_create.delay([
        relational.Assignment(
            visit_id=request.visit.pk,
            campaign_id=assignment.campaign.pk,
            content_id=assignment.content.pk,
            feature_type=assignment.feature_type,
            feature_row=assignment.feature_row,
            random_assign=assignment.random_assign,
            chosen_from_table=assignment.chosen_from_table,
            chosen_from_rows=assignment.chosen_from_rows,
        )
        for assignment in notification_user.assignments.iterator()
    ])

    page_styles = utils.assign_page_styles(
        request.visit,
        relational.Page.FRAME_FACES,
        campaign,
        content,
    )

    return render(request, 'targetshare/faces_email_friends.html', {
        'fb_params': fb_params,
        'msg_params': msg_params,
        'campaign': campaign,
        'content': content,
        'properties': campaign.campaignproperties.get(),
        'campaign_css': page_styles,
        'all_friends': all_friends,
        'face_friends': face_friends,
        'show_faces': show_faces,
        'user': user,
        'num_face': num_face,
    })


@csrf_exempt
def canvas(request):
    return render(request, 'targetshare/canvas.html')


@csrf_exempt
def canvas_faces(request, **kws):
    return frame_faces(request, canvas=True, **kws)
