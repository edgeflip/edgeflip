import logging
import re
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

from core.utils import campaignstatus
from core.utils.http import JsonHttpResponse

from targetshare import forms
from targetshare.integration import facebook
from targetshare.models import datastructs, dynamo, relational
from targetshare.tasks import db, targeting
from targetshare.tasks.integration.facebook import extend_token
from targetshare.views import FACES_TASKS_KEY, OAUTH_TASK_KEY, PENDING_EXCLUSIONS_KEY, utils


LOG = logging.getLogger('crow')

MAX_FACES = 50


def request_targeting(visit, token, api, campaign, client_content, num_faces):
    """Kick off targeting tasks and record event.

    Returns a ranked sequence of as many parallel tasks as targeting uses for the
    given API version.

    Note that initiated tasks are assumed to be complementary; the lowest-ranked
    task is required, while higher-ranked tasks are considered refinements.
    Upon the frontend's "last call", the successfully-generated results of the
    *last* task in this sequence are used; and, in preceding calls, if the
    *first* task is found to have failed, the backend will immediately return
    what it has to the front-end. (See `faces`.)

    """
    if api >= 2:
        task = targeting.targeted_network.delay(
            token=token,
            visit_id=visit.pk,
            campaign_id=campaign.pk,
            content_id=client_content.pk,
            num_faces=num_faces,
        )
        tasks = [(None, task)]
        content = "task_id: {}".format(task.task_id)
    else:
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
        tasks = [(3, task_px3), (4, task_px4)]
        content = "px3_task_id: {}, px4_task_id: {}".format(task_px3.id, task_px4.id),

    visit.events.create(
        event_type='targeting_requested',
        campaign_id=campaign.pk,
        client_content_id=client_content.pk,
        content=content,
    )
    return tasks


@csrf_exempt # FB posts directly to this view
@utils.encoded_endpoint
@utils.require_visit
def frame_faces(request, api, campaign_id, content_id):
    campaign = get_object_or_404(relational.Campaign, campaign_id=campaign_id)
    campaign_properties = campaign.campaignproperties.get()

    if campaign_properties.root_campaign_id != campaign_properties.campaign_id:
        LOG.warning("Received request for non-root campaign", extra={'request': request})
        raise http.Http404

    try:
        campaign_status = campaignstatus.handle_request(request, campaign, campaign_properties)
    except campaignstatus.DisallowedError as exc:
        return exc.make_error_response(embedded=True)

    client = campaign.client
    content = get_object_or_404(client.clientcontent, content_id=content_id)
    canvas = bool(re.search(r'\bcanvas\b', request.resolver_match.namespace))

    db.bulk_create.delay([
        relational.Event(
            visit_id=request.visit.pk,
            event_type='faces_page_load',
            campaign_id=campaign.pk,
            client_content_id=content.pk,
            content=api,
        ),
        relational.Event(
            visit_id=request.visit.pk,
            event_type=('faces_canvas_load' if canvas else 'faces_iframe_load'),
            campaign_id=campaign.pk,
            client_content_id=content.pk,
            content=api,
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
                faces_tasks_key = FACES_TASKS_KEY.format(api=api,
                                                         campaign_id=campaign_id,
                                                         content_id=content_id,
                                                         fbid=token.fbid)
                if faces_tasks_key not in request.session:
                    # Initiate targeting tasks:
                    targeting_tasks = request_targeting(
                        visit=request.visit,
                        token=token,
                        api=api,
                        campaign=campaign,
                        client_content=content,
                        num_faces=campaign_properties.num_faces,
                    )
                    request.session[faces_tasks_key] = [
                        (rank, task.id) for (rank, task) in targeting_tasks
                    ]

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
            reverse('targetshare:outgoing', args=[client.fb_app_id, value]),
            urllib.urlencode({'campaignid': campaign_id}),
        )

    default_permissions = client.fb_app.permissions.values_list('code', flat=True)

    return render(request, 'targetshare/frame_faces.html', {
        'fb_params': {
            'fb_app_name': client.fb_app.name,
            'fb_app_id': client.fb_app_id,
        },
        'api': api,
        'default_scope': ','.join(default_permissions.iterator()),
        'campaign': campaign,
        'content': content,
        'properties': properties,
        'campaign_css': page_styles,
        'canvas': canvas,
        'draft_preview': campaign_status.isdraft,
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
        return JsonHttpResponse(faces_form.errors, status=400)

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
        return JsonHttpResponse({
            'status': 'waiting',
            'reason': "Cookies are required. Please try again.",
            'campaignid': campaign.pk,
            'contentid': content.pk,
        }, status=202)

    faces_tasks_key = FACES_TASKS_KEY.format(api=data['api'],
                                             campaign_id=campaign.pk,
                                             content_id=content.pk,
                                             fbid=data['fbid'])
    targeting_task_ids = request.session.get(faces_tasks_key)

    if targeting_task_ids:
        # Retrieve statuses of active targeting tasks #
        ranked_tasks = [(rank, celery.current_app.AsyncResult(task_id))
                        for (rank, task_id) in targeting_task_ids]
    else:
        # First request #
        token = datastructs.ShortToken(
            fbid=data['fbid'],
            appid=client.fb_app_id,
            token=data['token'],
            api=data['api'],
        )

        # Extend & store Token and record authorized UserClient:
        extend_token.delay(*token)
        db.get_or_create.delay(
            relational.UserClient,
            client_id=client.pk,
            fbid=data['fbid'],
        )

        # Initiate targeting tasks:
        ranked_tasks = request_targeting(
            visit=request.visit,
            token=token,
            api=data['api'],
            campaign=campaign,
            client_content=content,
            num_faces=data['num_face'],
        )
        targeting_task_ids = [(rank, task.id) for (rank, task) in ranked_tasks]
        request.session[faces_tasks_key] = targeting_task_ids

    (targeting_ranks, targeting_tasks) = zip(*ranked_tasks)

    # Check status #
    (primary_rank, primary_task) = ranked_tasks[0]
    if not all(task.ready() for task in targeting_tasks) and not primary_task.failed() and not data['last_call']:
        return JsonHttpResponse({
            'status': 'waiting',
            'reason': "Identifying friends.",
            'campaignid': campaign.pk,
            'contentid': content.pk,
        }, status=202)

    # Select results #
    ranked_results = [
        (rank, task.result if task.successful() else targeting.empty_filtering_result)
        for (rank, task) in ranked_tasks
    ]
    # Choose the filtered results from the highest-ranked results:
    for (result_rank, targeting_result) in reversed(ranked_results):
        if targeting_result.filtered:
            # Let's use this result set;
            # but, gather ranking data from the others as well.
            for (complement_rank, complement_result) in ranked_results:
                if complement_result is not targeting_result and complement_result.ranked:
                    if complement_rank > result_rank:
                        # Trust higher-ranked complement's results ranking:
                        targeting_result = targeting_result._replace(
                            ranked=complement_result.ranked,
                            filtered=targeting_result.filtered.reranked(complement_result.ranked,
                                                                        result_rank),
                        )
                    else:
                        # Our ranking is best;
                        # just include lower-ranked complement's scores (for reporting):
                        targeting_result = targeting_result._replace(
                            filtered=targeting_result.filtered.rescored(complement_result.ranked,
                                                                        complement_rank),
                        )

            # We're done
            break

    if not targeting_result.ranked or not targeting_result.filtered:
        if (
            primary_task.failed() and
            isinstance(primary_task.result, facebook.utils.OAuthPermissionDenied) and
            primary_task.result.requires_review
        ):
            return JsonHttpResponse({
                'status': 'failed',
                'reason': "This app has not been approved by Facebook, and is only accessible "
                          "to admins, developers and the app's test users.\n\n"
                          "If you are a Facebook App reviewer, please log in as "
                          '"Open Graph Test User" and try again.',
            }, status=403)
        elif primary_task.ready():
            return http.HttpResponseServerError('No friends were identified for you.')
        else:
            LOG.fatal("primary targeting task (px%s) failed to complete in the time allotted (%s)",
                      primary_rank or 0, primary_task.task_id, extra={'request': request})
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
        reverse('targetshare:objects', kwargs={
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
        'fb_app_name': client.fb_app.name,
        'fb_app_id': client.fb_app_id,
        'fb_object_title': fb_attrs.og_title,
        'fb_object_image': fb_attrs.og_image,
        'fb_object_description': fb_attrs.og_description
    }

    # Record generation of suggestions (but only once per set of tasks):
    generated = []
    gen_count = 0
    for tier in targeting_result.filtered:
        for edge in itertools.islice(tier['edges'], MAX_FACES - gen_count):
            ranked_scores = (
                # ((pretty rank), (pretty score))
                (('' if rank is None else rank), ('N/A' if score is None else score))
                for (rank, score) in ((rank, edge.get_rank_score(rank)) for rank in targeting_ranks)
            )
            px_content = ', '.join(
                "px{}_score: {} ({})".format(rank, score, task.task_id)
                for ((rank, score), task) in zip(ranked_scores, targeting_tasks)
            )
            generated.append({
                'visit_id': request.visit.visit_id,
                'campaign_id': tier['campaign_id'],
                'client_content_id': tier['content_id'],
                'friend_fbid': edge.secondary.fbid,
                'event_type': 'generated',
                'content': u"{} : {}".format(px_content, edge.secondary.name),
                'defaults': {
                    'event_datetime': timezone.now(),
                },
            })

        gen_count = len(generated)
        if gen_count >= MAX_FACES:
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
    mapped_task_ids = dict(targeting_task_ids)
    eligible_edges = (edge for edge in targeting_result.filtered.iteredges()
                      if edge.secondary.fbid is None or edge.secondary.fbid not in all_exclusions)
    for (edge_index, edge) in enumerate(itertools.islice(eligible_edges, MAX_FACES)):
        if edge_index >= data['num_face']:
            face_friends.append(edge.secondary)
        else:
            show_faces.append(edge.secondary)

            try:
                (score_rank, score) = edge.get_score()
            except LookupError:
                score = 'N/A'
                score_rank = primary_rank

            px_content = "px{}_score: {} ({})".format(
                '' if score_rank is None else score_rank,
                score,
                mapped_task_ids[score_rank],
            )

            shown.append(
                relational.Event(
                    visit_id=request.visit.visit_id,
                    campaign_id=campaign.campaign_id,
                    client_content_id=content.content_id,
                    friend_fbid=edge.secondary.fbid,
                    content=u"{} : {}".format(px_content, edge.secondary.name),
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

    return JsonHttpResponse({
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
    all_friends = dynamo.User.items.batch_get(
        keys=LazyList({'fbid': fbid} for fbid in friend_fbids.iterator())
    )
    shown_fbids = set(
        notification_user.events.filter(
            event_type='shown',
        ).values_list('friend_fbid', flat=True).iterator()
    )
    num_face = len(shown_fbids)

    (face_friends, show_faces) = ([], [])
    for friend in all_friends:
        if friend.fbid in shown_fbids:
            show_faces.append(friend)
        else:
            face_friends.append(friend)

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
        reverse('targetshare:objects', kwargs={
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
        'fb_app_name': client.fb_app.name,
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
