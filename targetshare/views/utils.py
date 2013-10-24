import logging
import functools
import os.path

from django import http
from django.conf import settings
from django.shortcuts import _get_queryset
from django.template import TemplateDoesNotExist
from django.template.loader import find_template

from targetshare import models, utils
from targetshare.tasks import db

LOG = logging.getLogger(__name__)


def get_client_ip(request):
    """Return the user agent IP address for the given request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_visitor(request, fbid=None):
    """Return the Visitor object for the request.

    Visitors are unique humans, identified by `fbid`, when available; when the `fbid`
    is unavailable, the visitor UUID, stored in a long-term cookie (see
    settings.VISITOR_COOKIE_NAME), is used.

    When neither the `fbid` is known nor a UUID cookie is found, (and in the edge case
    that the `fbid` is known, is not yet linked to a visitor, and conflicts with the
    visitor identified by cookie), a new visitor is created. Existing visitors are
    updated with their `fbid`, once it is discovered.

    As long as the returned visitor is linked to the current visit, and the
    VisitorMiddleware is installed, the user agent's visitor cookie will be kept up
    to date.

    Arguments:
        request: The Django request object
        fbid: The Facebook user identifier (optional)

    """
    # Ensure fbid type for comparisons:
    fbid = long(fbid) if fbid else None

    if fbid:
        # fbid trumps UUID:
        try:
            return models.relational.Visitor.objects.get(fbid=fbid)
        except models.relational.Visitor.DoesNotExist:
            pass

    uuid = request.COOKIES.get(settings.VISITOR_COOKIE_NAME)

    if uuid:
        visitor, created = models.relational.Visitor.objects.get_or_create(
            uuid=uuid,
            defaults={'fbid': fbid},
        )
        if created or not fbid or fbid == visitor.fbid:
            # No (possibility for) fbid conflict -- we're done.
            return visitor
        elif not visitor.fbid:
            # Update visitor with now-known fbid:
            visitor.fbid = fbid
            db.delayed_save.delay(visitor, update_fields=['fbid'])
            return visitor

    # Either UUID is empty or points to Visitor with conflicting fbid.
    # Make a new visitor.
    if fbid:
        # get_or_create to handle race:
        visitor, _created = models.relational.Visitor.objects.get_or_create(fbid=fbid)
        return visitor
    else:
        return models.relational.Visitor.objects.create()


def set_visit(request, app_id, fbid=None, start_event=None):
    """Set the Visit object for the request.

    Visits are unique per session (`session_key`) and application (`app_id`), and
    are required to log Events. This helper ensures a session, a Visit and a
    "session start" event have been created, and updates the Visit with data that
    may not be supplied on session start (such as `fbid`).

    Arguments:
        request: The Django request object
        app_id: The Facebook application identifier
        fbid: The Facebook user identifier (optional)
        start_event: A dict of additional data for the session start event,
            (e.g. `campaign`) (optional)

    """
    # Ensure we have a valid session
    if request.session.session_key:
        # Don't trust existing; ensure unexpired session has loaded:
        request.session._get_session()
    else:
        # Force a session and key to be created:
        request.session.save()

    creation_values = [
        ('ip', get_client_ip(request)),
        ('referer', request.META.get('HTTP_REFERER', '')[:1028]),
        ('user_agent', request.META.get('HTTP_USER_AGENT', '')[:1028]),
    ]
    updating_values = [
        ('source', request.REQUEST.get('efsrc', '')),
        ('visitor', get_visitor(request, fbid)),
    ]

    request.visit, created = models.relational.Visit.objects.get_or_create(
        session_id=request.session.session_key,
        app_id=long(app_id),
        defaults=dict(creation_values + updating_values),
    )
    if created:
        # Add start event:
        db.delayed_save.delay(
            models.relational.Event(
                visit=request.visit,
                event_type='session_start',
                **(start_event or {})
            )
        )
    else:
        # Update visit with values not known on or changed since creation:
        updates = {key: value for key, value in updating_values
                   if value and getattr(request.visit, key) != value}
        if updates:
            for key, value in updates.items():
                setattr(request.visit, key, value)
            db.delayed_save.delay(request.visit, update_fields=updates.keys())


def get_object_or_none(klass, **kws):
    queryset = _get_queryset(klass)
    try:
        return queryset.get(**kws)
    except (queryset.model.DoesNotExist, ValueError):
        return None


def require_visit(view):
    """Decorator manufacturing a view wrapper, which requires a Visit for the request.

    The Visit is added to the request at attribute "visit"::

        @_require_visit
        def my_view(request, campaign_id, content_id):
            visit = request.visit
            ...

    An app, Campaign, ClientContent or FBObject must be specified via the path or query
    string, for identification of Client app. Facebook ID (fbid) is retrieved from the
    query string, if available.

    Campaign and ClientContent, if appropriate, are recommended, for completeness of the
    new Visit's "session start" Event.

    """
    @functools.wraps(view)
    def wrapped_view(request, *args, **kws):
        # Gather info from path and query string
        campaign_id = kws.get('campaign_id', request.REQUEST.get('campaignid'))
        content_id = kws.get('content_id', request.REQUEST.get('contentid'))
        fb_object_id = kws.get('fb_object_id')
        fbid = request.REQUEST.get('fbid') or request.REQUEST.get('userid') or None
        app_id = kws.get('app_id', request.REQUEST.get('appid'))

        # Determine client, and campaign & client content if available
        client = campaign = client_content = None

        if campaign_id:
            campaign = get_object_or_none(models.Campaign, campaign_id=campaign_id)
            client = campaign and campaign.client
        if content_id:
            client_content = get_object_or_none(models.ClientContent, content_id=content_id)
            client = client_content.client if (client_content and not client) else client
        if fb_object_id and client is None:
            client = get_object_or_none(models.Client, fbobjects__fb_object_id=fb_object_id)

        if not app_id:
            if client is None:
                return http.HttpResponseBadRequest("The application could not be determined")
            else:
                app_id = client.fb_app_id

        # Initialize Visit and add to request
        set_visit(request, app_id, fbid, {
            'campaign': campaign,
            'client_content': client_content,
        })
        return view(request, *args, **kws)

    return wrapped_view


def encoded_endpoint(view):
    """Decorator manufacturing an endpoint for the given view which additionally
    accepts a slug encoding the campaign and content IDs.

    """
    @functools.wraps(view)
    def wrapped_view(request, campaign_id=None, content_id=None,
                     campaign_slug=None, **kws):
        # TODO: Disallow non-campaign_slug route (i.e. with campaign_id+content_id)
        # TODO: except in _test_mode.
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
                    "{}() requires keyword argument 'campaign_slug' or arguments "
                    "'campaign_id' and 'content_id'".format(view.__name__)
                )

        return view(request, campaign_id=campaign_id, content_id=content_id, **kws)

    return wrapped_view


def locate_client_template(client, template_name):
    """Attempt to locate a given template in the client's template path.

    If none is found, the default template is returned.

    """
    try:
        templates = find_template('targetshare/clients/%s/%s' % (
            client.codename,
            template_name
        ))

    except TemplateDoesNotExist:
        # hopefully template_name is correctly set
        return 'targetshare/%s' % template_name

    else:
        return templates[0].name


def locate_client_css(client, css_name):
    """Attempt to locate a given css file in the static path.

    If none is found, the default is returned.

    """
    client_path = os.path.join('css', 'clients', client.codename, css_name)
    if os.path.exists(os.path.join(settings.STATIC_ROOT, client_path)):
        return os.path.join(settings.STATIC_URL, client_path)
    else:
        return os.path.join(settings.STATIC_URL, 'css', css_name)


def test_mode(request):
    """Return whether the request may be put into "test mode"."""
    return request.GET.get('secret') == settings.TEST_MODE_SECRET
