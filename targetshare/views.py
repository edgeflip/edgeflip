import functools
import json
import logging
import os.path
import random

import celery

from django import http
from django.conf import settings
from django.core.urlresolvers import reverse
from django.shortcuts import render, get_object_or_404
from django.template import RequestContext, TemplateDoesNotExist
from django.template.loader import find_template, render_to_string
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

from targetshare import (
    facebook,
    mock_facebook,
    models,
    utils,
)
from targetshare.tasks import db, ranking


LOG = logging.getLogger(__name__)


def _get_client_ip(request):
    """Return the user agent IP address for the given request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def _generate_session(request, campaign_id, content_id, fbid, app_id,
                     content_str=''):
    if not request.session.session_key:
        # Force a key to be created if it doesn't exist
        request.session.save()
        event = models.Event(
            session_id=request.session.session_key, campaign_id=campaign_id,
            client_content_id=content_id, ip=_get_client_ip(request),
            fbid=fbid, friend_fbid=None, event_type='session_start',
            app_id=app_id, content=content_str, activity_id=None
        )
        db.delayed_save.delay(event)

    return request.session.session_key


def _encoded_endpoint(view):
    """Decorator manufacturing an endpoint for the given view which additionally
    accepts a slug encoding the campaign and content IDs.

    """
    @functools.wraps(view)
    def wrapped_view(request, campaign_id=None, content_id=None,
                     campaign_slug=None, **kws):
        if not campaign_id or not content_id:
            if campaign_slug:
                try:
                    decoded = utils.decodeDES(campaign_slug)
                    campaign_id, content_id = (int(part) for part in decoded.split('/') if part)
                except (ValueError, TypeError):
                    LOG.exception('Failed to decrypt: %r', campaign_slug)
                    return http.HttpResponseNotFound()
            else:
                raise TypeError(
                    "{}() takes keyword argument 'campaign_slug' or arguments "
                    "'campaign_id' and 'content_id'".format(
                        view.__name__,
                    )
                )

        return view(request, campaign_id=campaign_id, content_id=content_id, **kws)

    return wrapped_view


def _locate_client_template(client, template_name):
    """Attempt to locate a given template in the client's template path.

    If none is found, the default template is returned.

    """
    try:
        templates = find_template('targetshare/clients/%s/%s' % (
            client.subdomain,
            template_name
        ))
    except TemplateDoesNotExist:
        return 'targetshare/%s' % template_name
    else:
        return templates[0].name


def _locate_client_css(client, css_name):
    """Attempt to locate a given css file in the static path.

    If none is found, the default is returned.

    """
    client_path = os.path.join('css', 'clients', client.subdomain, css_name)
    if os.path.exists(os.path.join(settings.STATIC_ROOT, client_path)):
        return os.path.join(settings.STATIC_URL, client_path)
    else:
        return os.path.join(settings.STATIC_URL, 'css', css_name)


def _test_mode(request):
    """Return whether the request may be put into "test mode"."""
    return request.GET.get('secret') == settings.TEST_MODE_SECRET


@_encoded_endpoint
def button(request, campaign_id, content_id):
    content = get_object_or_404(models.ClientContent, content_id=content_id)
    campaign = get_object_or_404(models.Campaign, campaign_id=campaign_id)
    client = campaign.client

    faces_url = campaign.campaignproperties_set.get().faces_url(content_id)
    params_dict = {
        'fb_app_name': client.fb_app_name, 'fb_app_id': client.fb_app_id
    }
    session_id = _generate_session(
        request, campaign.pk, content.pk, None, client.fb_app_id)

    # Use campaign-custom button style template name if one exists:
    try:
        # rand_assign raises ValueError if list is empty:
        style_recs = campaign.campaignbuttonstyle_set.all()
        style_exp_tupes = [
            (campaign_button_style.button_style_id, campaign_button_style.rand_cdf)
            for campaign_button_style in style_recs
        ]
        style_id = int(utils.rand_assign(style_exp_tupes))
        button_style_file = models.ButtonStyleFile.objects.get(button_style=style_id)
    except (ValueError, models.ButtonStyleFile.DoesNotExist):
        # The default template name will do:
        template_name = 'button.html'

        #set NULLs for the Assignment below
        style_id = None
        style_recs = []
    else:
        template_name = button_style_file.html_template

    # Record assignment:
    assignment = models.Assignment(
        session_id=session_id, campaign=campaign,
        content=content, feature_type='button_style_id',
        feature_row=style_id, random_assign=True,
        chosen_from_table='campaign_button_styles',
        chosen_from_rows=[campaign_button_style.button_style_id
                          for campaign_buton_style in style_recs],
    )
    db.delayed_save.delay(assignment)

    return render(request, _locate_client_template(client, template_name), {
        'fb_params': params_dict,
        'goto': faces_url,
        'client_css': _locate_client_css(client, 'edgeflip_client.css'),
        'client_css_simple': _locate_client_css(client, 'edgeflip_client_simple.css'),
        'campaign': campaign,
        'content': content,
        'session_id': session_id
    })


@csrf_exempt # FB posts directly to this view
@_encoded_endpoint
def frame_faces(request, campaign_id, content_id, canvas=False):
    content = get_object_or_404(models.ClientContent, content_id=content_id)
    campaign = get_object_or_404(models.Campaign, campaign_id=campaign_id)
    test_mode = _test_mode(request)
    client = campaign.client
    session_id = _generate_session(
        request, campaign.pk, content.pk, None, client.fb_app_id)
    event = models.Event(
        session_id=session_id, campaign_id=campaign_id,
        client_content_id=content_id, ip=_get_client_ip(request),
        fbid=None, friend_fbid=None, event_type='faces_page_load',
        app_id=client.fb_app_id, content='', activity_id=None
    )
    db.delayed_save.delay(event)

    if test_mode:
        try:
            test_fbid = int(request.GET['fbid'])
            test_token = request.GET['token']
        except (KeyError, ValueError):
            return http.HttpResponseBadRequest('Test mode requires numeric ID ("fbid") '
                                               'and Token ("token")')
    else:
        test_fbid = test_token = None

    return render(request, _locate_client_template(client, 'frame_faces.html'), {
        'fb_params': {
            'fb_app_name': client.fb_app_name,
            'fb_app_id': client.fb_app_id,
        },
        'campaign': campaign,
        'content': content,
        'properties': campaign.campaignproperties_set.get(),
        'client_css': _locate_client_css(client, 'edgeflip_client.css'),
        'client_css_simple': _locate_client_css(client, 'edgeflip_client_simple.css'),
        'test_mode': test_mode,
        'test_token': test_token,
        'test_fbid': test_fbid,
        'canvas': canvas,
    })


@require_POST
@csrf_exempt
def faces(request):
    fbid = request.POST.get('fbid')
    tok = request.POST.get('token')
    num_face = request.POST.get('num')
    content_id = request.POST.get('contentid')
    campaign_id = request.POST.get('campaignid')
    mock_mode = request.POST.get('mockmode', False)
    px3_task_id = request.POST.get('px3_task_id')
    px4_task_id = request.POST.get('px4_task_id')
    last_call = True if request.POST.get('last_call') else False
    edges_ranked = fbmodule = px4_edges = None

    if settings.ENV != 'production' and mock_mode:
        LOG.info('Running in mock mode')
        fbmodule = mock_facebook
        fbid = 100000000000 + random.randint(1, 10000000)
    else:
        fbmodule = facebook

    subdomain = request.get_host().split('.')[0]
    content = get_object_or_404(models.ClientContent, content_id=content_id)
    campaign = get_object_or_404(models.Campaign, campaign_id=campaign_id)
    properties = campaign.campaignproperties_set.get()
    client = campaign.client
    session_id = _generate_session(
        request, campaign_id, content_id, fbid, client.fb_app_id)
    ip = _get_client_ip(request)

    if mock_mode and subdomain != settings.WEB.mock_subdomain:
        return http.HttpResponseForbidden(
            'Mock mode only allowed for the mock client')

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
            if campaign_id and content_id:
                campaign = models.Campaign.objects.get(pk=campaign_id)
                content = models.ClientContent.objects.get(pk=content_id)
            px4_edges = px4_result.result if px4_result.successful() else ()
            if not all([edges_ranked, edges_filtered]):
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
        token = fbmodule.extendTokenFb(fbid, client.fb_app_id, tok)
        px3_task_id = ranking.proximity_rank_three(
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

    campaign.client.userclients.get_or_create(fbid=fbid)
    if px4_edges:
        edges_filtered = edges_filtered.reranked(px4_edges)

    return _apply_campaign(request, edges_ranked, edges_filtered,
                           best_cs_filter_id, choice_set_slug, subdomain,
                           campaign, content, session_id, ip, fbid,
                           int(num_face), properties)


def _apply_campaign(request, edges_ranked, edges_filtered, best_cs_filter,
                    choice_set_slug, subdomain, campaign, content, session_id,
                    ip, fbid, num_face, properties):

    max_faces = 50
    friend_dicts = [e.toDict() for e in edges_filtered.edges]
    face_friends = friend_dicts[:max_faces]
    all_friends = [e.toDict() for e in edges_ranked]
    client = campaign.client

    fb_object_recs = campaign.campaignfbobjects_set.all()
    fb_obj_exp_tupes = [(r.fb_object_id, r.rand_cdf) for r in fb_object_recs]
    fb_object_id = int(utils.rand_assign(fb_obj_exp_tupes))
    assignment = models.Assignment(
        session_id=session_id, campaign=campaign,
        content=content, feature_type='fb_object_id',
        feature_row=fb_object_id, random_assign=True,
        chosen_from_table='campaign_fb_objects',
        chosen_from_rows=[r.pk for r in fb_object_recs]
    )
    db.delayed_save.delay(assignment)

    fb_object = models.FBObject.objects.get(pk=fb_object_id)
    fb_attrs = fb_object.fbobjectattribute_set.get()
    msg_params = {
        'sharing_prompt': fb_attrs.sharing_prompt,
        'msg1_pre': fb_attrs.msg1_pre,
        'msg1_post': fb_attrs.msg1_post,
        'msg2_pre': fb_attrs.msg2_pre,
        'msg2_post': fb_attrs.msg2_post,
    }
    fb_object_url = 'https://%s%s?cssslug=%s' % (
        request.get_host(),
        reverse('objects', kwargs={
            'fb_object_id': fb_object_id, 'content_id': content.pk
        }),
        choice_set_slug
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
                    models.Event(
                        session_id=session_id, campaign_id=tier_campaignId,
                        client_content_id=tier_contentId, ip=ip, fbid=fbid,
                        friend_fbid=friend.secondary.id, event_type='generated',
                        app_id=fb_params['fb_app_id'], content=content_str,
                        activity_id=None
                    )
                )

            num_gen = num_gen - len(edges_list)

        if (num_gen <= 0):
            break

    for friend in face_friends[:num_face]:
        events.append(
            models.Event(
                session_id=session_id, campaign_id=campaign.pk,
                client_content_id=content.pk, ip=ip, fbid=fbid,
                friend_fbid=friend['id'], event_type='shown',
                app_id=fb_params['fb_app_id'], content=content_str,
                activity_id=None
            )
        )

    db.bulk_create.delay(events)

    return http.HttpResponse(
        json.dumps({
            'status': 'success',
            'html': render_to_string(_locate_client_template(client, 'faces_table.html'), {
                'msg_params': msg_params,
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

    if not redirect_url:
        return http.HttpResponseNotFound()

    fb_object_url = 'https://%s%s?cssslug=%s' % (
        request.get_host(),
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
        'fb_app_id': int(client.fb_app_id),
        'fb_object_title': fb_attrs.og_title,
        'fb_object_image': fb_attrs.og_image,
        'fb_object_description': fb_attrs.og_description,
        'fb_org_name': fb_attrs.org_name,
    }
    content_str = '%(fb_app_name)s:%(fb_object_type)s %(fb_object_url)s' % obj_params
    ip = _get_client_ip(request)
    session_id = _generate_session(
        request, None, content_id, None, client.fb_app_id, content_str)
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    if user_agent.find('facebookexternalhit') != -1:
        LOG.info(
            'Facebook crawled object %s with content %s from IP %s',
            fb_object_id, content_id, ip
        )
    else:
        event = models.Event(
            session_id=session_id, campaign=None,
            client_content_id=content_id,
            content=content_str, ip=ip, fbid=None,
            friend_fbid=None, event_type='clickback',
            app_id=client.fb_app_id, activity_id=action_id
        )
        db.delayed_save.delay(event)

    return render(request, 'targetshare/fb_object.html', {
        'fb_params': obj_params,
        'redirect_url': redirect_url,
        'content': content_str,
        'client': client,
    })


@require_POST
def suppress(request):
    user_id = request.POST.get('userid')
    app_id = request.POST.get('appid')
    campaign_id = request.POST.get('campaignid')
    content_id = request.POST.get('contentid')
    content = request.POST.get('content')
    old_id = request.POST.get('oldid')
    ip = _get_client_ip(request)
    session_id = _generate_session(
        request, campaign_id, content_id, user_id, app_id)

    new_id = request.POST.get('newid')
    fname = request.POST.get('fname')
    lname = request.POST.get('lname')

    event = models.Event(
        session_id=session_id, campaign_id=campaign_id,
        client_content_id=content_id, ip=ip, fbid=user_id,
        friend_fbid=old_id, event_type='suppress',
        app_id=app_id, content=content, activity_id=None
    )
    db.delayed_save.delay(event)
    exclusion = models.FaceExclusion(
        fbid=user_id, campaign_id=campaign_id,
        content_id=content_id, friend_fbid=old_id,
        reason='suppressed'
    )
    db.delayed_save.delay(exclusion)

    if new_id != '':
        event = models.Event(
            session_id=session_id, campaign_id=campaign_id,
            client_content_id=content_id, ip=ip, fbid=user_id,
            friend_fbid=new_id, event_type="shown",
            app_id=app_id, content=content, activity_id=None
        )
        db.delayed_save.delay(event)
        return render(request, 'targetshare/new_face.html', {
            'fbid': new_id,
            'firstname': fname,
            'lastname': lname
        })
    else:
        return http.HttpResponse()


@require_POST
def record_event(request):

    user_id = request.POST.get('userid')
    app_id = request.POST.get('appid')
    campaign_id = request.POST.get('campaignid')
    content_id = request.POST.get('contentid')
    content = request.POST.get('content')
    action_id = request.POST.get('actionid')
    friends = [int(fid) for fid in request.POST.getlist('friends[]')]

    event_type = request.POST.get('eventType')
    ip = _get_client_ip(request)
    session_id = _generate_session(
        request, campaign_id, content_id, user_id, app_id)
    single_occurrence_events = ['button_load', 'authorized']
    multi_occurrence_events = [
        'button_click', 'auth_fail', 'select_all_click',
        'share_click', 'share_fail', 'shared', 'clickback',
        'suggest_message_click',
    ]

    if event_type not in single_occurrence_events + multi_occurrence_events:
        return http.HttpResponseForbidden(
            "Ah, ah, ah. You didn't say the magic word"
        )

    if event_type in single_occurrence_events and event_type in request.session:
        # Already logged it
        return http.HttpResponse()

    events = []
    if friends:
        for friend in friends:
            events.append(
                models.Event(
                    session_id=session_id, campaign_id=campaign_id,
                    client_content_id=content_id, ip=ip, fbid=user_id,
                    friend_fbid=friend, event_type=event_type,
                    app_id=app_id, content=content, activity_id=action_id
                )
            )
    else:
        events.append(
            models.Event(
                session_id=session_id, campaign_id=campaign_id,
                client_content_id=content_id, ip=ip, fbid=user_id or None,
                event_type=event_type, app_id=app_id, content=content,
                activity_id=action_id, friend_fbid=None
            )
        )

    if events:
        db.bulk_create.delay(events)

        if event_type in single_occurrence_events:
            # Prevent dupe logging
            request.session[event_type] = True

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
            client = models.Client.objects.get(campaign__campaign_id=campaign_id)
        except models.Client.DoesNotExist:
            LOG.exception(
                "Failed to write authorization for fbid %r and token %r under "
                "campaign %r for non-existent client",
                fbid, token_string, campaign_id,
            )
            raise

        client.userclients.get_or_create(fbid=fbid)
        token = facebook.extendTokenFb(fbid, appid, token_string)
        token.save(overwrite=True)

    if event_type == 'shared':
        # If this was a share, write these friends to the exclusions table so
        # we don't show them for the same content/campaign again
        exclusions = []
        for friend in friends:
            exclusions.append(
                models.FaceExclusion(
                    fbid=user_id, campaign_id=campaign_id,
                    content_id=content_id, friend_fbid=friend,
                    reason='shared'
                )
            )

        if exclusions:
            db.bulk_create.delay(exclusions)

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
        share_message = models.ShareMessage(
            activity_id=action_id, fbid=user_id, campaign_id=campaign_id,
            content_id=content_id, message=share_msg
        )
        db.delayed_save.delay(share_message)

    return http.HttpResponse()


@csrf_exempt
def canvas(request):
    return render(request, 'targetshare/canvas.html')


@csrf_exempt
def canvas_faces(request, **kws):

    return frame_faces(request, canvas=True, **kws)


def health_check(request):
    if 'elb' in request.GET:
        return http.HttpResponse("It's Alive!", status=200)

    fb_resp = facebook.getUrlFb("http://graph.facebook.com/6963")
    return http.HttpResponse(
        json.dumps({
            'database': models.relational.Client.objects.exists(),
            'dynamo': bool(models.dynamo.User.items.table.describe()),
            'facebook': int(fb_resp['id']) == 6963,
        }),
        content_type='application/json',
    )
