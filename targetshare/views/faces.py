import logging
import urllib

import celery

from django import http
from django.core.urlresolvers import reverse
from django.shortcuts import render, get_object_or_404
from django.template import RequestContext
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from faraday.structs import LazyList

from targetshare import forms, models
from targetshare.integration import facebook
from targetshare.tasks import db, ranking
from targetshare.tasks.integration.facebook import extend_token
from targetshare.views import utils

LOG = logging.getLogger(__name__)


@csrf_exempt # FB posts directly to this view
@utils.encoded_endpoint
@utils.require_visit
def frame_faces(request, campaign_id, content_id, canvas=False):
    campaign = get_object_or_404(models.relational.Campaign, campaign_id=campaign_id)
    client = campaign.client
    content = get_object_or_404(client.clientcontent, content_id=content_id)

    db.bulk_create.delay([
        models.relational.Event(
            visit=request.visit,
            campaign=campaign,
            client_content=content,
            event_type='faces_page_load',
        ),
        models.relational.Event(
            visit=request.visit,
            campaign=campaign,
            client_content=content,
            event_type=('faces_canvas_load' if canvas else 'faces_iframe_load'),
        )
    ])

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
        html_template = filenames.html_template or 'frame_faces.html'
        css_template = filenames.css_file or 'edgeflip_client_simple.css'

    # Record assignment:
    db.delayed_save.delay(
        models.relational.Assignment.make_managed(
            visit=request.visit,
            campaign=campaign,
            content=content,
            feature_row=faces_style,
            chosen_from_rows=campaign.campaignfacesstyles,
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

    return render(request, utils.locate_client_template(client, html_template), {
        'fb_params': {
            'fb_app_name': client.fb_app_name,
            'fb_app_id': client.fb_app_id,
        },
        'campaign': campaign,
        'content': content,
        'properties': properties,
        'client_css': utils.locate_client_css(client, 'edgeflip_client.css'),
        'client_css_simple': utils.locate_client_css(client, css_template),
        'canvas': canvas,
        # Debug mode currently on for all methods of targetted sharing
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
    campaign = data['campaign']
    content = data['content']
    client = campaign.client

    if data['px3_task_id'] and data['px4_task_id']:
        # Check status of active ranking tasks:
        px3_result = celery.current_app.AsyncResult(data['px3_task_id'])
        px4_result = celery.current_app.AsyncResult(data['px4_task_id'])
        if (px3_result.ready() and px4_result.ready()) or data['last_call'] or px3_result.failed():
            (px3_edges_result, px4_edges_result) = (
                result.result if result.successful() else ranking.empty_filtering_result
                for result in (px3_result, px4_result)
            )
            if px4_edges_result.filtered is None:
                # px4 filtering didn't happen, so use px3
                if px4_edges_result.ranked is None or px3_edges_result.filtered is None:
                    # px4 ranking didn't happen either;
                    # or, it did but we have no px3 filtering result to rerank
                    # (in which case we can error out later):
                    edges_result = px3_edges_result
                else:
                    # Re-rank px3 edges by px4 ranking:
                    edges_result = px3_edges_result._replace(
                        ranked=px4_edges_result.ranked,
                        filtered=px3_edges_result.filtered.reranked(px4_edges_result.ranked)
                    )
            else:
                # px4 filtering completed, so use it:
                edges_result = px4_edges_result

            if edges_result.campaign_id and edges_result.campaign_id != campaign.pk:
                campaign = models.relational.Campaign.objects.get(pk=edges_result.campaign_id)
            if edges_result.content_id and edges_result.content_id != content.pk:
                content = models.relational.ClientContent.objects.get(pk=edges_result.content_id)

            if not edges_result.ranked or not edges_result.filtered:
                return http.HttpResponseServerError('No friends were identified for you.')

        else:
            return utils.JsonHttpResponse({
                'status': 'waiting',
                'px3_task_id': data['px3_task_id'],
                'px4_task_id': data['px4_task_id'],
                'campaignid': campaign.pk,
                'contentid': content.pk,
            })

    else:
        # First request #
        token = models.datastructs.ShortToken(
            fbid=data['fbid'],
            appid=client.fb_app_id,
            token=data['token'],
        )

        # Extend & store Token and record authorized UserClient:
        extend_token.delay(*token)
        db.get_or_create.delay(
            models.relational.UserClient,
            client_id=client.pk,
            fbid=data['fbid'],
        )

        # Initiate ranking tasks:
        px3_task = ranking.proximity_rank_three(
            token=token,
            visit_id=request.visit.pk,
            campaign_id=campaign.pk,
            content_id=content.pk,
            num_faces=data['num_face'],
        )
        px4_task = ranking.proximity_rank_four.delay(
            token=token,
            visit_id=request.visit.pk,
            campaign_id=campaign.pk,
            content_id=content.pk,
            num_faces=data['num_face'],
            px3_task_id=px3_task.id,
        )
        return utils.JsonHttpResponse({
            'status': 'waiting',
            'px3_task_id': px3_task.id,
            'px4_task_id': px4_task.id,
            'campaignid': campaign.pk,
            'contentid': content.pk,
        })

    # Apply campaign
    if data['efobjsrc']:
        fb_object = facebook.third_party.source_campaign_fbobject(campaign, data['efobjsrc'])
        db.delayed_save.delay(
            models.relational.Assignment.make_managed(
                visit=request.visit,
                campaign=campaign,
                content=content,
                feature_row=fb_object,
                chosen_from_rows=None,
                manager=campaign.campaignfbobjects,
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
            'cssslug': edges_result.choice_set_slug,
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
    LOG.debug('fb_object_url: %s', fb_params['fb_object_url'])
    content_str = '%s:%s %s' % (
        fb_params['fb_app_name'],
        fb_params['fb_object_type'],
        fb_params['fb_object_url']
    )

    num_gen = max_faces = 50
    events = []
    for tier in edges_result.filtered:
        edges_list = tier['edges'][:num_gen]
        tier_campaign_id = tier['campaign_id']
        tier_content_id = tier['content_id']
        for edge in edges_list:
            events.append(
                models.relational.Event(
                    visit=request.visit,
                    campaign_id=tier_campaign_id,
                    client_content_id=tier_content_id,
                    friend_fbid=edge.secondary.fbid,
                    event_type='generated',
                    content=content_str,
                )
            )
        num_gen -= len(edges_list)
        if num_gen <= 0:
            break

    face_friends = edges_result.filtered.secondaries[:max_faces]
    for friend in face_friends[:data['num_face']]:
        events.append(
            models.relational.Event(
                visit=request.visit,
                campaign_id=campaign.pk,
                client_content_id=content.pk,
                friend_fbid=friend.fbid,
                content=content_str,
                event_type='shown',
            )
        )

    db.bulk_create.delay(events)

    return utils.JsonHttpResponse({
        'status': 'success',
        'campaignid': campaign.pk,
        'contentid': content.pk,
        'html': render_to_string(utils.locate_client_template(client, 'faces_table.html'), {
            'msg_params': {
                'sharing_prompt': fb_attrs.sharing_prompt,
                'sharing_sub_header': fb_attrs.sharing_sub_header,
                'msg1_pre': fb_attrs.msg1_pre,
                'msg1_post': fb_attrs.msg1_post,
                'msg2_pre': fb_attrs.msg2_pre,
                'msg2_post': fb_attrs.msg2_post,
            },
            'fb_params': fb_params,
            'all_friends': tuple(edge.secondary for edge in edges_result.ranked),
            'face_friends': face_friends,
            'show_faces': face_friends[:data['num_face']],
            'num_face': data['num_face'],
        }, context_instance=RequestContext(request)),
    })


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
    utils.set_visit(request, client.fb_app_id, notification_user.fbid, {
        'campaign': campaign,
        'client_content': content,
    })

    # Gather friend data
    user = models.User.items.get_item(fbid=notification_user.fbid)
    friend_fbids = notification_user.events.filter(
        event_type__in=('generated', 'shown')
    ).values_list('friend_fbid', flat=True).distinct()
    face_friends = all_friends = models.User.items.batch_get(
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

    return render(request, utils.locate_client_template(client, 'faces_email_friends.html'), {
        'fb_params': fb_params,
        'msg_params': msg_params,
        'campaign': campaign,
        'content': content,
        'properties': campaign.campaignproperties.get(),
        'client_css': utils.locate_client_css(client, 'edgeflip_client.css'),
        'client_css_simple': utils.locate_client_css(client, 'edgeflip_client_simple.css'),
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
