import json
import logging
import random
import urllib

import celery

from django import http
from django.conf import settings
from django.core.urlresolvers import reverse
from django.shortcuts import render, get_object_or_404
from django.template import RequestContext
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

from targetshare import models
from targetshare.integration import facebook
from targetshare.tasks import db, ranking
from targetshare.views import utils

LOG = logging.getLogger(__name__)


@csrf_exempt # FB posts directly to this view
@utils._encoded_endpoint
@utils._require_visit
def frame_faces(request, campaign_id, content_id, canvas=False):
    campaign = get_object_or_404(models.relational.Campaign, campaign_id=campaign_id)
    client = campaign.client
    content = get_object_or_404(client.clientcontent, content_id=content_id)
    test_mode = utils._test_mode(request)
    db.delayed_save.delay(
        models.relational.Event(
            visit=request.visit,
            campaign=campaign,
            client_content=content,
            event_type='faces_page_load',
        )
    )

    if test_mode:
        try:
            test_fbid = int(request.GET['fbid'])
            test_token = request.GET['token']
        except (KeyError, ValueError):
            return http.HttpResponseBadRequest('Test mode requires numeric ID ("fbid") '
                                               'and Token ("token")')
    else:
        test_fbid = test_token = None

    # Use campaign-custom template name if one exists:
    try:
        # rand_assign raises ValueError if list is empty:
        faces_style = campaign.campaignfacesstyles.random_assign()
        filenames = faces_style.facesstylefiles.get()
    except (ValueError, models.relational.FacesStyleFiles.DoesNotExist):
        # The default template name will do:
        faces_style = None
        html_template = 'frame_faces.html'
        css_template = 'edgeflip_client_simple.css'
    else:
        html_template = filenames.html_template or 'button.html'
        css_template = filenames.css_file or 'edgeflip_client_simple.css'

    # Record assignment:
    db.delayed_save.delay(
        models.relational.Assignment.make_managed(
            visit=request.visit,
            campaign=campaign,
            content=content,
            assignment=faces_style,
            manager=campaign.campaignfacesstyles,
        )
    )

    properties = campaign.campaignproperties.values().get()
    for override_key, field in [
        ('efsuccessurl', 'client_thanks_url'),
        ('eferrorurl', 'client_error_url'),
    ]:
        value = request.REQUEST.get(override_key) or properties[field]
        properties[field] = "{}?{}".format(
            reverse('outgoing', args=[client.fb_app_id, urllib.quote_plus(value)]),
            urllib.urlencode({'campaignid': campaign_id}),
        )

    return render(request, utils._locate_client_template(client, html_template), {
        'fb_params': {
            'fb_app_name': client.fb_app_name,
            'fb_app_id': client.fb_app_id,
        },
        'campaign': campaign,
        'content': content,
        'properties': properties,
        'client_css': utils._locate_client_css(client, 'edgeflip_client.css'),
        'client_css_simple': utils._locate_client_css(client, css_template),
        'test_mode': test_mode,
        'test_token': test_token,
        'test_fbid': test_fbid,
        'canvas': canvas,
        # Debug mode currently on for all methods of targetted sharing
        # However will likely just reflect the canvas var in the future
        'debug_mode': True,
    })


@require_POST
@csrf_exempt
@utils._require_visit
def faces(request):
    fbid = request.POST.get('fbid')
    token_string = request.POST.get('token')
    num_face = int(request.POST['num'])
    content_id = request.POST.get('contentid')
    campaign_id = request.POST.get('campaignid')
    fbobject_source_url = request.POST.get('efobjsrc')
    mock_mode = request.POST.get('mockmode', False)
    px3_task_id = request.POST.get('px3_task_id')
    px4_task_id = request.POST.get('px4_task_id')
    last_call = bool(request.POST.get('last_call'))
    edges_ranked = px4_edges = None

    if settings.ENV != 'production' and mock_mode:
        LOG.info('Running in mock mode')
        fb_client = facebook.mock_client
        fbid = 100000000000 + random.randint(1, 10000000)
    else:
        fb_client = facebook.client

    subdomain = request.get_host().split('.')[0]
    campaign = get_object_or_404(models.relational.Campaign, campaign_id=campaign_id)
    client = campaign.client
    content = get_object_or_404(client.clientcontent, content_id=content_id)

    if mock_mode and subdomain != settings.WEB.mock_subdomain:
        return http.HttpResponseForbidden('Mock mode only allowed for the mock client')

    if px3_task_id and px4_task_id:
        px3_result = celery.current_app.AsyncResult(px3_task_id)
        px4_result = celery.current_app.AsyncResult(px4_task_id)
        if (px3_result.ready() and px4_result.ready()) or last_call or px3_result.failed():
            if px3_result.successful():
                px3_result_result = px3_result.result
            else:
                px3_result_result = (None,) * 6
            (
                edges_ranked,
                edges_filtered,
                best_cs_filter_id,
                choice_set_slug,
                campaign_id,
                content_id,
            ) = px3_result_result
            if campaign_id:
                campaign = models.relational.Campaign.objects.get(pk=campaign_id)
            if content_id:
                content = models.relational.ClientContent.objects.get(pk=content_id)
            px4_edges = px4_result.result if px4_result.successful() else ()
            if not edges_ranked or not edges_filtered:
                return http.HttpResponse('No friends identified for you.', status=500)
        else:
            return http.HttpResponse(
                json.dumps({
                    'status': 'waiting',
                    'px3_task_id': px3_task_id,
                    'px4_task_id': px4_task_id,
                    'campaignid': campaign_id,
                    'contentid': content_id,
                }),
                status=200,
                content_type='application/json'
            )
    else:
        token = fb_client.extendTokenFb(long(fbid), client.fb_app_id, token_string)
        db.delayed_save(token, overwrite=True)
        px3_task_id = ranking.proximity_rank_three(
            mock_mode=mock_mode,
            token=token,
            fbid=fbid,
            visit_id=request.visit.pk,
            campaignId=campaign_id,
            contentId=content_id,
            numFace=num_face,
        ).id
        px4_task = ranking.proximity_rank_four.delay(mock_mode, fbid, token)
        return http.HttpResponse(json.dumps(
            {
                'status': 'waiting',
                'px3_task_id': px3_task_id,
                'px4_task_id': px4_task.id,
                'campaignid': campaign_id,
                'contentid': content_id,
            }),
            status=200,
            content_type='application/json'
        )

    client.userclients.get_or_create(fbid=fbid)
    if px4_edges:
        edges_filtered = edges_filtered.reranked(px4_edges)

    # Apply campaign
    max_faces = 50
    friend_dicts = [e.toDict() for e in edges_filtered.edges]
    face_friends = friend_dicts[:max_faces]
    all_friends = [e.toDict() for e in edges_ranked]

    if fbobject_source_url:
        fb_object = facebook.third_party.source_campaign_fbobject(campaign, fbobject_source_url)
        db.delayed_save.delay(
            models.relational.Assignment.make_managed(
                visit=request.visit,
                campaign=campaign,
                content=content,
                assignment=fb_object,
                manager=campaign.campaignfbobjects,
                options=None,
                random_assign=False,
            )
        )
    else:
        fb_object = campaign.campaignfbobjects.for_datetime().random_assign()
        db.delayed_save.delay(
            models.relational.Assignment.make_managed(
                visit=request.visit,
                campaign=campaign,
                content=content,
                assignment=fb_object,
                manager=campaign.campaignfbobjects,
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
            'cssslug': choice_set_slug,
            'campaign_id': campaign_id,
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
    LOG.debug('fb_object_url: %s', fb_params['fb_object_url'])
    content_str = '%s:%s %s' % (
        fb_params['fb_app_name'],
        fb_params['fb_object_type'],
        fb_params['fb_object_url']
    )

    num_gen = max_faces
    events = []
    for tier in edges_filtered:
        edges_list = tier['edges']
        tier_campaignId = tier['campaignId']
        tier_contentId = tier['contentId']

        if len(edges_list) > num_gen:
            edges_list = edges_list[:num_gen]

        if edges_list:
            for friend in edges_list:
                events.append(
                    models.relational.Event(
                        visit=request.visit,
                        campaign_id=tier_campaignId,
                        client_content_id=tier_contentId,
                        friend_fbid=friend.secondary.id,
                        event_type='generated',
                        content=content_str,
                    )
                )
            num_gen = num_gen - len(edges_list)

        if num_gen <= 0:
            break

    for friend in face_friends[:num_face]:
        events.append(
            models.relational.Event(
                visit=request.visit,
                campaign_id=campaign.pk,
                client_content_id=content.pk,
                friend_fbid=friend['id'],
                content=content_str,
                event_type='shown',
            )
        )

    db.bulk_create.delay(events)

    return http.HttpResponse(
        json.dumps({
            'status': 'success',
            'html': render_to_string(utils._locate_client_template(client, 'faces_table.html'), {
                'msg_params': {
                    'sharing_prompt': fb_attrs.sharing_prompt,
                    'msg1_pre': fb_attrs.msg1_pre,
                    'msg1_post': fb_attrs.msg1_post,
                    'msg2_pre': fb_attrs.msg2_pre,
                    'msg2_post': fb_attrs.msg2_post,
                },
                'fb_params': fb_params,
                'all_friends': all_friends,
                'face_friends': face_friends,
                'show_faces': face_friends[:num_face],
                'num_face': num_face
            }, context_instance=RequestContext(request)),
            'campaignid': campaign.pk,
            'contentid': content.pk,
        }),
        status=200
    )


def faces_email_friends(request, notification_uuid):
    ''' A view that's fairly similar to our Faces/Frame Faces views, except
    that this will not perform any crawls. We've already done the crawling
    in the background, so we can skip that here, and instead leverage the
    friends passed in via GET params.
    '''
    # Campaign setup
    notification_user = get_object_or_404(
        models.NotificationUser,
        uuid=notification_uuid
    )
    campaign = notification_user.notification.campaign
    content = notification_user.notification.client_content
    client = campaign.client
    request.visit = utils._get_visit(request, client.fb_app_id, notification_user.fbid, {
        'campaign': campaign,
        'client_content': content,
    })

    # Gather friend data
    shown_events = set(notification_user.events.filter(
        event_type='shown').values_list('friend_fbid', flat=True))
    num_face = len(shown_events)
    user_obj = models.User.items.get_item(fbid=notification_user.fbid)
    friend_objs = models.User.items.batch_get(
        keys=[{'fbid': x} for x in notification_user.events.filter(
            event_type__in=('generated', 'shown')).values_list(
                'friend_fbid', flat=True).distinct()]
    )

    user = models.datastructs.UserInfo.from_dynamo(user_obj)
    face_friends = all_friends = [
        models.datastructs.Edge(
            user, models.datastructs.UserInfo.from_dynamo(x), None, None
        ).toDict() for x in friend_objs
    ]
    show_faces = [
        x for x in face_friends if x['id'] in shown_events
    ]
    db.delayed_save.delay(
        models.Event(
            visit=request.visit,
            campaign_id=campaign.pk,
            client_content_id=content.pk,
            event_type='faces_email_page_load',
        )
    )

    # FBObj setup
    fb_object = campaign.campaignfbobjects.for_datetime().random_assign()
    db.delayed_save.delay(
        models.relational.Assignment.make_managed(
            visit=request.visit,
            campaign=campaign,
            content=content,
            assignment=fb_object,
            manager=campaign.campaignfbobjects,
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
    events = []
    for event in notification_user.events.all():
        events.append(
            models.Event(
                visit=request.visit,
                campaign_id=event.campaign.pk,
                client_content_id=event.client_content.pk,
                friend_fbid=event.friend_fbid,
                content=content_str,
                event_type=event.event_type,
            )
        )

    assignments = []
    for assignment in notification_user.assignments.all():
        assignments.append(
            models.Assignment(
                visit=request.visit,
                campaign=assignment.campaign,
                content=assignment.content,
                feature_type=assignment.feature_type,
                feature_row=assignment.feature_row,
                random_assign=assignment.random_assign,
                chosen_from_table=assignment.chosen_from_table,
                chosen_from_rows=assignment.chosen_from_rows
            )
        )
    db.bulk_create.delay(events)
    db.bulk_create.delay(assignments)

    return render(request, utils._locate_client_template(client, 'faces_email_friends.html'), {
        'fb_params': fb_params,
        'msg_params': msg_params,
        'campaign': campaign,
        'content': content,
        'properties': campaign.campaignproperties.get(),
        'client_css': utils._locate_client_css(client, 'edgeflip_client.css'),
        'client_css_simple': utils._locate_client_css(client, 'edgeflip_client_simple.css'),
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
