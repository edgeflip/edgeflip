import json
import logging
import random
import datetime

from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.http import (
    HttpResponse,
    HttpResponseNotFound,
    HttpResponseForbidden
)
from django.views.decorators.http import require_POST

from targetshare import (
    celery,
    datastructs,
    facebook,
    mock_facebook,
    models,
    tasks,
    utils,
)
from targetshare.settings import config


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

    properties = campaign.campaignproperties_set.get()
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
        style_exp_tupes = [(x.button_id, x.rand_cdf) for x in style_recs]
        style_id = int(utils.rand_assign(style_exp_tupes))
        models.Assignment.objects.create(
            session_id=session_id, campaign=campaign,
            content=content, feature_type='button_style_id',
            feature_row=style_id, random_assign=True,
            chosen_from_table='campaign_button_styles',
            chosen_from_rows=[x.button_id for x in style_recs]
        )
        button_style = models.ButtonStyle.objects.get(pk=style_id)
        style_template = button_style.buttonstylefile_set.get().html_template
    except:
        style_template = 'button.html'

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
        campaign_id, content_id = [int(i) for i in decoded.split('/')]
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

    return render(request, 'frame_faces.html', {
        'fb_params': params_dict,
        'campaign': campaign,
        'content': content,
        'properties': campaign.campaignproperties_set.get()
    })


@require_POST
@csrf_exempt
def faces(request):
    fbid = request.POST.get('fbid')
    tok = request.POST.get('token')
    num_face = request.POST.get('num')
    content_id = request.POST.get('contentid')
    campaign_id = request.POST.get('campaignid')
    mock_mode = request.POST.get('mock_mode', False)
    px3_task_id = request.POST.get('px3_task_id')
    px4_task_id = request.POST.get('px4_task_id')
    session_id = request.POST.get('session_id') or request.session.session_key
    last_call = True if request.POST.get('last_call') else False
    edges_ranked = fbmodule = px4_edges = None

    if mock_mode:
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
    client = campaign.client
    if not _validate_client_subdomain(campaign, content, subdomain):
        return HttpResponseNotFound()

    if mock_mode and subdomain != config.web.mock_subdomain:
        return HttpResponseForbidden(
            'Mock mode only allowed for the mock client')

    properties = campaign.campaignproperties_set.get()
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
        px3_result = celery.celery.AsyncResult(px3_task_id)
        px4_result = celery.celery.AsyncResult(px4_task_id)
        if (px3_result.ready() and (px4_result.ready() or last_call)):
            px4_edges = px4_result.result if px4_result.successful() else []
            edges_ranked, best_cs_filter, choice_set, allow_generic, campaign_id, content_id = px3_result.result
            if not all([edges_ranked, best_cs_filter, choice_set]):
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
                        'campaign_id': campaign_id,
                        'content_id': content_id,
                    }),
                    status=200,
                    content_type='application/json'
                )
    else:
        px3_task_id = tasks.proximity_rank_three(
            mock_mode=mock_mode,
            token=token,
            subdomain=subdomain,
            campaign_id=campaign_id,
            content_id=content_id,
            ip=ip,
            fbid=fbid,
            num_face=num_face,
            properties=properties
        )
        px4_task_id = tasks.proximity_rank_four.delay(
            mock_mode, fbid, token)
        return HttpResponse(json.dumps(
            {
                'status': 'waiting',
                'px3_task_id': px3_task_id,
                'px4_task_id': px4_task_id,
                'campaign_id': campaign_id,
                'content_id': content_id,
            }),
            status=200,
            content_type='application/json'
        )

    models.UserClient.objects.get_or_create(
        fbid=fbid, client=campaign.client
    )
    if px4_edges:
        filtered_px4_edges = []
        filtered_px3_edge_ids = [x.secondary.id for x in best_cs_filter[1]]
        for edge in px4_edges:
            if edge.secondary.id in filtered_px3_edge_ids:
                filtered_px4_edges.append(edge)

        best_cs_filter = (best_cs_filter[0], filtered_px4_edges)

    return apply_campaign(request, edges_ranked, best_cs_filter, choice_set,
                          allow_generic, subdomain, campaign, content,
                          session_id, ip, fbid, num_face, properties)


def apply_campaign(request, edges_ranked, best_cs_filter, choice_set,
                   allow_generic, subdomain, campaign, content, session_id,
                   ip, fbid, num_face, properties):
    friend_dicts = [e.toDict() for e in best_cs_filter[1]]
    face_friends = friend_dicts[:num_face]
    all_friends = friend_dicts[:50]
    pick_dicts = [e.toDict() for e in edges_ranked]

    choice_set_slug = best_cs_filter[0].urlSlug if best_cs_filter[0] else allow_generic[1]
    if best_cs_filter[0] is None:
        logger.debug("Generic returned for %s with campaign %s." % (
            fbid, campaign.pk
        ))
        models.Assignment.objects.create(
            session_id=session_id, campaign=campaign,
            content=content, feature_type='generic choice set filter',
            feature_row=None, random_assign=False,
            chosen_from_table='choice_set_filters',
            chosen_from_rows=[csf.choiceSetFilterId for csf in choice_set.choiceSetfilters]
        )
    else:
        models.Assignment.objects.create(
            session_id=session_id, campaign=campaign,
            content=content, feature_type='filter_id',
            feature_row=best_cs_filter[0].filterId, random_assign=False,
            chosen_from_table='choice_set_filters',
            chosen_from_rows=[csf.choiceSetFilterId for csf in choice_set.choiceSetfilters]
        )

    fb_object_recs = campaign.campaignfbobject_set.all()
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
    action_params = {
        'fb_action_type': fb_attrs.og_action,
        'fb_object_type': fb_attrs.og_type,
        'fb_object_url': 'INSERT REVERSE URL', # XXX: FIXME
        'fb_app_name': properties.fb_app_name,
        'fb_app_id': properties.fb_app_id,
        'fb_object_title': fb_attrs.og_title,
        'fb_object_image': fb_attrs.og_image,
        'fb_object_description': fb_attrs.og_description
    }
    logger.debug('fb_object_url: %s', action_params['fb_object_url'])
    content = '%s:%s %s' % (
        action_params['fb_app_name'],
        action_params['fb_object_type'],
        action_params['fb_object_url']
    )

    for friend in face_friends:
        models.Event.objects.create(
            session_id=session_id, campaign=campaign, content=content,
            ip=ip, fbid=fbid,
            friend_fbid=friend['id'], event_type='shown',
            app_id=action_params['fb_app_id'], conent=content, acvitiy_id=None
        )

    return HttpResponse(
        json.dumps({
            'status': 'success',
            'html': render(request, 'face_table.html', {
                'all_friends': all_friends,
                'msg_params': msg_params,
                'action_params': action_params,
                'face_friends': face_friends,
                'pick_friends': pick_dicts,
                'num_friends': num_face
            }),
            'campaign': campaign,
            'content': content,
        }),
        status=200
    )


def objects(request, fb_object_id, content_id):

    fb_object = get_object_or_404(models.FBObject, fb_object_id=fb_object_id)
    content = get_object_or_404(
        models.ClientContent, client_content_id=content_id
    )
    client = fb_object.client
    fb_attrs = fb_object.fbobjectattributes_set.get()
    choice_set_slug = request.GET.get('cssslug', '')
    action_id = request.GET.get('fb_action_ids', '').split(',')[0].strip()
    action_id = int(action_id) if action_id else None
    fb_object_slug = fb_attrs.url_slug
    redirect_url = client.clientcontent_set.get().url

    if not redirect_url:
        return HttpResponseNotFound()

    obj_params = {
        'page_title': fb_attrs.page_title,
        'fb_action_type': fb_attrs.og_action,
        'fb_object_type': fb_attrs.og_type,
        'fb_object_url': 'INSERT REVERSE URL', # XXX: FIXME
        'fb_app_name': client.fb_app_name,
        'fb_app_id': client.fb_app_id,
        'fb_object_title': fb_attrs.og_title,
        'fb_object_image': fb_attrs.og_image,
        'fb_object_description': fb_attrs.og_description
    }
    content = '%(fb_app_name)s:%(fb_object_type)s %(fb_object_url)s' % obj_params
    ip = 'blah' # XXX FIXME
    user_agent = 'blah' # XXX FIXME
    if user_agent.find('facebookexternalhit') != -1:
        logger.info(
            'Facebook crawled object %s with content %s from IP %s',
            fb_object_id, content_id, ip
        )
    else:
        models.Event.objects.create(
            session_id=request.session.id, campaign=None, content=content,
            ip=ip, fbid=None,
            friend_fbid=None, event_type='clickback',
            app_id=client.fb_app_id, acvitiy_id=None
        )

    return render(request, 'fb_object.html', {
        'fb_params': obj_params,
        'reidrect_url': redirect_url,
        'content': content
    })


@require_POST
def suppress(request):
    user_id = request.POST.get('userid')
    app_id = request.POST.get('appid')
    campaign_id = request.POST.get('campaignid')
    content_id = request.POST.get('contentid')
    content = request.POST.get('content')
    old_id = request.POST.get('oldid')
    session_id = request.session.id
    ip = 'fixme' # XXX: FIXME

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
        return render(request, 'new_face.html', {
            'id': new_id,
            'fname': fname,
            'lname': lname
        })
    else:
        return HttpResponse()


@require_POST
def record_event(request):

    user_id = request.POST.get('userid')
    app_id = request.POST.get('appid')
    campaign_id = request.POST.get('campaignid')
    content_id = request.POST.get('contentid')
    content = request.POST.get('content')
    action_id = request.POST.get('actionid')
    friends = [int(f) for f in request.POST.get('friends', [])]
    event_type = request.POST.get('eventType')
    session_id = request.session.id
    ip = 'fixme' # XXX: FIXME

    if (event_type not in [
        'button_load', 'button_click', 'authorized', 'auth_fail',
        'select_all_click', 'suggest_message_click',
        'share_click', 'share_fail', 'shared', 'clickback'
    ]):
        return HttpResponseForbidden(
            "Ah, ah, ah. You didn't say the magic word"
        )

    for friend in friends:
        models.Event.objects.create(
            session_id=session_id, campaign_id=campaign_id,
            client_content_id=content_id, ip=ip, fbid=user_id,
            friend_fbid=friend, event_type=event_type,
            app_id=app_id, content=content, activity_id=action_id
        )

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
        for friend in friends:
            models.FaceExclusion.objects.create(
                fbid=user_id, campaign_id=campaign_id,
                content=content_id, friend_fbid=friend,
                reason='shared'
            )

    error_msg = request.POST.get('errorMsg')
    if error_msg:
        # may want to push these to the DB at some point, but at least for now,
        # dump them to the logs to ensure we keep the data.
        logger.error(
            'Front-end error encountered for user %s in session %s: %s',
            user_id, request.session.id, error_msg
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
