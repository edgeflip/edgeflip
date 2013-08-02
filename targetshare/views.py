import json
import logging
import random
import datetime

import celery

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import (
    HttpResponse,
    HttpResponseNotFound,
    HttpResponseForbidden
)
from django.shortcuts import render, get_object_or_404
from django.template import RequestContext
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from targetshare import (
    datastructs,
    facebook,
    mock_facebook,
    models,
    tasks,
    utils,
)


logger = logging.getLogger(__name__)


def _validate_client_subdomain(campaign, content, subdomain):
    ''' Verifies that the content and campaign clients are the same, and that
    the subdomain received matches what we expect on the client model
    '''

    valid = True
    if campaign.client_id != content.client_id:
        valid = False

    if campaign.client.subdomain != subdomain:
        valid = False

    return valid


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def button_encoded(request, campaign_slug):

    try:
        decoded = utils.decodeDES(campaign_slug)
        campaign_id, content_id = [int(i) for i in decoded.split('/')]
    except:
        logger.exception('Failed to decrypt button')
        return HttpResponseNotFound()

    return button(request, campaign_id, content_id)


def button(request, campaign_id, content_id):
    subdomain = request.get_host().split('.')[0]
    content = get_object_or_404(models.ClientContent, content_id=content_id)
    campaign = get_object_or_404(models.Campaign, campaign_id=campaign_id)
    client = campaign.client
    if not _validate_client_subdomain(campaign, content, subdomain):
        return HttpResponseNotFound()

    faces_url = campaign.campaignproperties_set.get().faces_url(content_id)
    params_dict = {
        'fb_app_name': client.fb_app_name, 'fb_app_id': client.fb_app_id
    }
    if not request.session.session_key:
        # Force a key to be created if it doesn't exist
        request.session.save()
    session_id = request.session.session_key

    style_template = None
    try:
        style_recs = campaign.campaignbuttonstyle_set.all()
        style_exp_tupes = [(x.button_style_id, x.rand_cdf) for x in style_recs]
        style_id = int(utils.rand_assign(style_exp_tupes))
        models.Assignment.objects.create(
            session_id=session_id, campaign=campaign,
            content=content, feature_type='button_style_id',
            feature_row=style_id, random_assign=True,
            chosen_from_table='campaign_button_styles',
            chosen_from_rows=[x.button_style_id for x in style_recs]
        )
        button_style = models.ButtonStyle.objects.get(pk=style_id)
        style_template = button_style.buttonstylefile_set.get().html_template
    except:
        style_template = 'targetshare/button.html'

    return render(request, style_template, {
        'fb_params': params_dict,
        'goto': faces_url,
        'campaign': campaign,
        'content': content,
        'session_id': session_id
    })


def frame_faces_encoded(request, campaign_slug):

    try:
        decoded = utils.decodeDES(campaign_slug)
        campaign_id, content_id = [int(i) for i in decoded.split('/') if i]
    except:
        logger.exception('Exception on decrypting frame_faces')
        return HttpResponseNotFound()

    return frame_faces(request, campaign_id, content_id)


def frame_faces(request, campaign_id, content_id):
    subdomain = request.get_host().split('.')[0]
    content = get_object_or_404(models.ClientContent, content_id=content_id)
    campaign = get_object_or_404(models.Campaign, campaign_id=campaign_id)
    if not _validate_client_subdomain(campaign, content, subdomain):
        return HttpResponseNotFound()

    client = campaign.client
    params_dict = {
        'fb_app_name': client.fb_app_name,
        'fb_app_id': client.fb_app_id
    }

    return render(request, 'targetshare/frame_faces.html', {
        'fb_params': params_dict,
        'campaign': campaign,
        'content': content,
        'properties': campaign.campaignproperties_set.get()
    })


@require_POST
@csrf_exempt # FIXME
def faces(request):
    fbid = request.POST.get('fbid')
    tok = request.POST.get('token')
    num_face = request.POST.get('num')
    content_id = request.POST.get('contentid')
    campaign_id = request.POST.get('campaignid')
    mock_mode = request.POST.get('mockmode', False)
    px3_task_id = request.POST.get('px3_task_id')
    px4_task_id = request.POST.get('px4_task_id')
    session_id = request.POST.get('session_id') or request.session.session_key
    last_call = True if request.POST.get('last_call') else False
    edges_ranked = fbmodule = px4_edges = None

    if settings.ENV != 'production' and mock_mode:
        logger.info('Running in mock mode')
        fbmodule = mock_facebook
        fbid = 100000000000 + random.randint(1, 10000000)
    else:
        fbmodule = facebook

    subdomain = request.get_host().split('.')[0]
    if not session_id:
        request.session.save()
        session_id = request.session.session_key
    ip = get_client_ip(request)
    content = get_object_or_404(models.ClientContent, content_id=content_id)
    campaign = get_object_or_404(models.Campaign, campaign_id=campaign_id)
    properties = campaign.campaignproperties_set.get()
    client = campaign.client
    if not _validate_client_subdomain(campaign, content, subdomain):
        return HttpResponseNotFound()

    if mock_mode and subdomain != settings.WEB.mock_subdomain:
        return HttpResponseForbidden(
            'Mock mode only allowed for the mock client')

    token = datastructs.TokenInfo(
        tok, fbid,
        int(client.fb_app_id),
        datetime.datetime.now()
    )
    token = fbmodule.extendTokenFb(
        fbid, token,
        int(client.fb_app_id) or token
    )

    if px3_task_id and px4_task_id:
        px3_result = celery.current_app.AsyncResult(px3_task_id)
        px4_result = celery.current_app.AsyncResult(px4_task_id)
        if (px3_result.ready() and (px4_result.ready() or last_call)):
            px4_edges = px4_result.result if px4_result.successful() else []
            edges_ranked, edges_filtered, best_cs_filter_id, choice_set_slug, campaign_id, content_id = px3_result.result
            if not all([edges_ranked, best_cs_filter_id, choice_set_slug]):
                return HttpResponse('No friends identified for you.', status=500)
        else:
            if last_call and not px3_result.ready():
                return HttpResponse('No friends identified for you.', status=500)
            else:
                return HttpResponse(
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
        px3_task_id = tasks.proximity_rank_three(
            mock_mode=mock_mode,
            token=token,
            clientSubdomain=subdomain,
            campaignId=campaign_id,
            contentId=content_id,
            sessionId=session_id,
            ip=ip,
            fbid=fbid,
            numFace=num_face,
            paramsDB=client
        )
        px4_task = tasks.proximity_rank_four.delay(
            mock_mode, fbid, token)
        return HttpResponse(json.dumps(
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

    models.UserClient.objects.get_or_create(
        fbid=fbid, client=campaign.client
    )
    if px4_edges:
        edges_filtered.rerankEdges(px4_edges)

    return apply_campaign(request, edges_ranked, edges_filtered,
                          best_cs_filter_id, choice_set_slug, subdomain,
                          campaign, content, session_id, ip, fbid,
                          int(num_face), properties)


def apply_campaign(request, edges_ranked, edges_filtered, best_cs_filter,
                   choice_set_slug, subdomain, campaign, content, session_id,
                   ip, fbid, num_face, properties):

    max_friends = 50
    friend_dicts = [e.toDict() for e in edges_filtered.edges()]
    face_friends = friend_dicts[:num_face]
    all_friends = friend_dicts[:max_friends]
    pick_dicts = [e.toDict() for e in edges_ranked]

    fb_object_recs = campaign.campaignfbobjects_set.all()
    fb_obj_exp_tupes = [(r.fb_object_id, r.rand_cdf) for r in fb_object_recs]
    fb_object_id = int(utils.rand_assign(fb_obj_exp_tupes))
    models.Assignment.objects.create(
        session_id=session_id, campaign=campaign,
        content=content, feature_type='fb_object_id',
        feature_row=fb_object_id, random_assign=True,
        chosen_from_table='campaign_fb_objects',
        chosen_from_rows=[r.pk for r in fb_object_recs]
    )

    fb_object = models.FBObject.objects.get(pk=fb_object_id)
    fb_attrs = fb_object.fbobjectattribute_set.get()
    msg_params = {
        'sharing_prompt': fb_attrs.sharing_prompt,
        'msg1_pre': fb_attrs.msg1_pre,
        'msg1_post': fb_attrs.msg1_post,
        'msg2_pre': fb_attrs.msg2_pre,
        'msg2_post': fb_attrs.msg2_post,
    }
    fb_object_url = '%s?cssslug=%s' % (
        reverse('objects', kwargs={
            'fb_object_id': fb_object_id, 'content_id': content.pk
        }),
        choice_set_slug
    )

    action_params = {
        'fb_action_type': fb_attrs.og_action,
        'fb_object_type': fb_attrs.og_type,
        'fb_object_url': fb_object_url,
        'fb_app_name': campaign.client.fb_app_name,
        'fb_app_id': campaign.client.fb_app_id,
        'fb_object_title': fb_attrs.og_title,
        'fb_object_image': fb_attrs.og_image,
        'fb_object_description': fb_attrs.og_description
    }
    logger.debug('fb_object_url: %s', action_params['fb_object_url'])
    content_str = '%s:%s %s' % (
        action_params['fb_app_name'],
        action_params['fb_object_type'],
        action_params['fb_object_url']
    )

    num_gen = max_friends
    for tier in edges_filtered.tiers:
        edges_list = tier['edges'][:]
        tier_campaignId = tier['campaignId']
        tier_contentId = tier['contentId']

        if len(edges_list) > num_gen:
            edges_list = edges_list[:num_gen]

        if edges_list:
            events = []
            for friend in edges_list:
                events.append(
                    models.Event(
                        session_id=session_id, campaign_id=tier_campaignId,
                        client_content_id=tier_contentId, ip=ip, fbid=fbid,
                        friend_fbid=friend.secondary.id, event_type='shown',
                        app_id=action_params['fb_app_id'], content=content_str,
                        activity_id=None
                    )
                )
            models.Event.objects.bulk_create(events)
            num_gen = num_gen - len(edges_list)

        if (num_gen <= 0):
            break

    return HttpResponse(
        json.dumps({
            'status': 'success',
            'html': render_to_string('targetshare/faces_table.html', {
                'all_friends': all_friends,
                'msg_params': msg_params,
                'action_params': action_params,
                'face_friends': face_friends,
                'pick_friends': pick_dicts,
                'num_friends': num_face
            }, context_instance=RequestContext(request)),
            'campaignid': campaign.pk,
            'contentid': content.pk,
        }),
        status=200
    )


def objects(request, fb_object_id, content_id):

    fb_object = get_object_or_404(models.FBObject, fb_object_id=fb_object_id)
    content = get_object_or_404(
        models.ClientContent, content_id=content_id
    )
    client = fb_object.client
    fb_attrs = fb_object.fbobjectattribute_set.get()
    choice_set_slug = request.GET.get('cssslug', '')
    action_id = request.GET.get('fb_action_ids', '').split(',')[0].strip()
    action_id = int(action_id) if action_id else None
    redirect_url = content.url
    if not request.session.session_key:
        # Force a key to be created if it doesn't exist
        request.session.save()
    session_id = request.session.session_key

    if not redirect_url:
        return HttpResponseNotFound()

    fb_object_url = '%s?cssslug=%s' % (
        reverse('objects', kwargs={
            'fb_object_id': fb_object_id, 'content_id': content_id
        }),
        choice_set_slug
    )
    obj_params = {
        'page_title': fb_attrs.page_title,
        'fb_action_type': fb_attrs.og_action,
        'fb_object_type': fb_attrs.og_type,
        'fb_object_url': fb_object_url,
        'fb_app_name': client.fb_app_name,
        'fb_app_id': client.fb_app_id,
        'fb_object_title': fb_attrs.og_title,
        'fb_object_image': fb_attrs.og_image,
        'fb_object_description': fb_attrs.og_description
    }
    content = '%(fb_app_name)s:%(fb_object_type)s %(fb_object_url)s' % obj_params
    ip = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    if user_agent.find('facebookexternalhit') != -1:
        logger.info(
            'Facebook crawled object %s with content %s from IP %s',
            fb_object_id, content_id, ip
        )
    else:
        models.Event.objects.create(
            session_id=session_id, campaign=None,
            content=content, ip=ip, fbid=None,
            friend_fbid=None, event_type='clickback',
            app_id=client.fb_app_id, activity_id=action_id
        )

    return render(request, 'targetshare/fb_object.html', {
        'fb_params': obj_params,
        'redirect_url': redirect_url,
        'content': content
    })


@require_POST
@csrf_exempt # FIXME
def suppress(request):
    user_id = request.POST.get('userid')
    app_id = request.POST.get('appid')
    campaign_id = request.POST.get('campaignid')
    content_id = request.POST.get('contentid')
    content = request.POST.get('content')
    old_id = request.POST.get('oldid')
    ip = get_client_ip(request)
    if not request.session.session_key:
        # Force a key to be created if it doesn't exist
        request.session.save()
    session_id = request.session.session_key

    new_id = request.POST.get('newid')
    fname = request.POST.get('fname')
    lname = request.POST.get('lname')

    models.Event.objects.create(
        session_id=session_id, campaign_id=campaign_id,
        client_content_id=content_id, ip=ip, fbid=user_id,
        friend_fbid=old_id, event_type='suppress',
        app_id=app_id, content=content, activity_id=None
    )
    models.FaceExclusion.objects.create(
        fbid=user_id, campaign_id=campaign_id,
        content_id=content_id, friend_fbid=old_id,
        reason='suppressed'
    )

    if new_id != '':
        models.Event.objects.create(
            session_id=session_id, campaign_id=campaign_id,
            client_content_id=content_id, ip=ip, fbid=user_id,
            friend_fbid=old_id, event_type="shown",
            app_id=app_id, content=content, activity_id=None
        )
        return render(request, 'targetshare/new_face.html', {
            'fbid': new_id,
            'firstname': fname,
            'lastname': lname
        })
    else:
        return HttpResponse()


@require_POST
@csrf_exempt # FIXME
def record_event(request):

    user_id = request.POST.get('userid')
    app_id = request.POST.get('appid')
    campaign_id = request.POST.get('campaignid')
    content_id = request.POST.get('contentid')
    content = request.POST.get('content')
    action_id = request.POST.get('actionid')
    friends = [int(f) for f in request.POST.get('friends', [])]
    event_type = request.POST.get('eventType')
    ip = get_client_ip(request)
    if not request.session.session_key:
        # Force a key to be created if it doesn't exist
        request.session.save()
    session_id = request.session.session_key

    if event_type not in [
        'button_load', 'button_click', 'authorized', 'auth_fail',
        'select_all_click', 'suggest_message_click',
        'share_click', 'share_fail', 'shared', 'clickback'
    ]:
        return HttpResponseForbidden(
            "Ah, ah, ah. You didn't say the magic word"
        )

    events = []
    for friend in friends:
        events.append(
            models.Event(
                session_id=session_id, campaign_id=campaign_id,
                client_content_id=content_id, ip=ip, fbid=user_id,
                friend_fbid=friend, event_type=event_type,
                app_id=app_id, content=content, activity_id=action_id
            )
        )

    if events:
        models.Event.objects.bulk_create(events)

    if event_type == 'authorized':
        tok = request.POST.get('token')
        try:
            client = models.Client.objects.get(
                campaign__campaign_id=campaign_id)
        except models.Client.DoesNotExist:
            client = None

        if client:
            models.UserClient.objects.create(
                fbid=user_id, client=client
            )
            user = datastructs.UserInfo(
                user_id, None, None, None, None, None, None, None
            )
            token = datastructs.TokenInfo(
                tok, user_id, int(app_id), datetime.datetime.now()
            )
            token = facebook.extendToken(user_id, token, int(app_id)) or token
            models.Token.objects.filter(
                fbid=user.id, app_id=token.appId, owner_id=token.ownerId,
                token=token.tok
            ).update(expires=token.expires)
        else:
            logger.error(
                "Trying to write an authorization for fbid %s with "
                "token %s for non-existent client", user_id, tok
            )

    if event_type == 'shared':
        # If this was a share, write these friends to the exclusions table so
        # we don't show them for the same content/campaign again
        exclusions = []
        for friend in friends:
            exclusions.append(
                models.FaceExclusion(
                    fbid=user_id, campaign_id=campaign_id,
                    content=content_id, friend_fbid=friend,
                    reason='shared'
                )
            )

        if exclusions:
            models.FaceExclusion.objects.bulk_create(exclusions)

    error_msg = request.POST.get('errorMsg')
    if error_msg:
        # may want to push these to the DB at some point, but at least for now,
        # dump them to the logs to ensure we keep the data.
        logger.error(
            'Front-end error encountered for user %s in session %s: %s',
            user_id, request.session.session_key, error_msg
        )

    share_msg = request.POST.get('shareMsg')
    if share_msg:
        models.ShareMessage.objects.create(
            activity_id=action_id, fbid=user_id, campaign_id=campaign_id,
            content_id=content_id, message=share_msg
        )

    return HttpResponse()


def canvas(request):

    return render(request, 'canvas.html')


def health_check(request):

    if 'elb' in request.GET:
        return HttpResponse("It's Alive!", status=200)

    components = {
        'database': False,
        'facebook': False
    }
    try:
        components['database'] = models.Client.objects.exists()
    except:
        raise

    try:
        fb_resp = facebook.getUrlFb("http://graph.facebook.com/6963")
        components['facebook'] = int(fb_resp['id']) == 6963
    except:
        raise

    return HttpResponse(
        json.dumps(components), content_type='application/json'
    )
