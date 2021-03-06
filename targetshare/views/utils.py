import functools
import logging
import urlparse

import django.core.cache
from django import http
from django.conf import settings
from django.shortcuts import _get_queryset

from core.utils import encryptedslug
from core.utils.decorators import ViewDecorator

from targetshare import models, utils
from targetshare.tasks import db


LOG = logging.getLogger(__name__)


def faces_url(client_faces_url, campaign, content, *multi, **extra):
    """Construct the complete faces frame URL for the given campaign's base URL."""
    url = urlparse.urlparse(client_faces_url)
    query = http.QueryDict(url.query, mutable=True)
    slug = encryptedslug.make_slug(campaign, content)
    extra.update(efcmpgslug=slug)
    query.update(*multi, **extra)
    full_url = url._replace(query=query.urlencode())
    return full_url.geturl()


def get_client_ip(request):
    """Return the user agent IP address for the given request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR', '')
    ips = (ip.strip() for ip in x_forwarded_for.split(','))
    try:
        return next(ip for ip in ips if ip)
    except StopIteration:
        return request.META.get('REMOTE_ADDR')


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


def set_visit(request, app_id, fbid=None, start_event=None, cycle=False):
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
        cycle: Force a new session (and visit); session data is carried over
            (optional)

    """
    # Ensure we have a valid session
    session_key0 = request.session.session_key
    if session_key0:
        # Don't trust existing; ensure unexpired session has loaded:
        request.session._get_session()

        if cycle and request.session.session_key == session_key0:
            # New session key required; force:
            request.session.cycle_key()
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
                visit_id=request.visit.visit_id,
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


def sget(dicts, anykeys=(), default=None):
    """Find any of the given keys in any of the given dicts.

    Returns the value of the first key found in the first dict in which
    it was found.

    """
    for dict_ in dicts:
        for key in anykeys:
            try:
                return dict_[key]
            except KeyError:
                pass
    return default


class require_visit(ViewDecorator):
    """View-wrapping decorator which requires generation of a Visit for the request.

    The Visit is added to the request at attribute "visit"::

        @require_visit
        def my_view(request, campaign_id, content_id):
            visit = request.visit
            ...

    An app, Campaign, ClientContent or FBObject must be specified via the path or query
    string, for identification of Client app. Facebook ID (fbid) is retrieved from the
    query string, if available.

    Campaign and ClientContent, if appropriate, are recommended, for completeness of the
    new Visit's "session start" Event.

    """
    @classmethod
    def configured(cls, **defaults):
        return functools.partial(cls, defaults=defaults)

    def __init__(self, view, defaults=None):
        super(require_visit, self).__init__(view)
        self.defaults = {} if defaults is None else defaults

    def __call__(self, request, *args, **kws):
        # Gather info from path and query string;
        # search both the view kws (path params) and REQUEST
        # (query params) for any fitting aliases:
        datasources = (kws, request.REQUEST, self.defaults)
        app_id = sget(datasources, ('app_id', 'appid'))
        campaign_id = sget(datasources, ('campaign_id', 'campaign', 'campaignid'))
        content_id = sget(datasources, ('content_id', 'content', 'contentid'))
        fbid = sget((request.REQUEST,), ('fbid', 'userid'))
        fb_object_id = kws.get('fb_object_id')

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
                LOG.warning("Could not determine Facebook application for request", extra={
                    'request': request,
                    'stack': True,
                })
                return http.HttpResponseBadRequest("The application could not be determined")

            app_id = client.fb_app_id

        # Initialize Visit and add to request
        set_visit(request, app_id, fbid, {
            'campaign': campaign,
            'client_content': client_content,
        })
        return self._view(request, *args, **kws)


class encoded_endpoint(ViewDecorator):
    """Decorator manufacturing an endpoint for the given view which additionally
    accepts a slug encoding the api and campaign and content IDs.

    """
    def __call__(self,
                 request,
                 api=None, campaign_id=None, content_id=None,
                 encrypted_slug=None,
                 **kws):
        if not encrypted_slug and not (api and campaign_id and content_id):
            raise TypeError(
                "{}() requires keyword argument 'encrypted_slug' or arguments "
                "'api', 'campaign_id' and 'content_id'".format(self.__name__)
            )

        try:
            if encrypted_slug:
                params = encryptedslug.get_params(encrypted_slug)
            else:
                params = encryptedslug.clean_params(api, campaign_id, content_id)
        except (ValueError, TypeError):
            LOG.exception('Failed to parse encoded endpoint params')
            raise http.Http404
        else:
            (api, campaign_id, content_id) = params

        return self._view(request, api=api, campaign_id=campaign_id, content_id=content_id, **kws)


def assign_page_styles(visit, page_code, campaign, content=None):
    """Randomly assign a set of stylesheets to the page for the given campaign,
    and record that assignment.

    Database results are cached according to the `PAGE_STYLE_CACHE_TIMEOUT` setting.

    """
    # Look up PageStyles:
    cache_key = 'campaignpagestylesets|{}|{}'.format(page_code, campaign.pk)
    options = django.core.cache.cache.get(cache_key)
    if options is None:
        # Retrieve from DB:
        campaign_page_style_sets = campaign.campaignpagestylesets.filter(
            page_style_set__page_styles__page__code=page_code,
        ).values_list('pk', 'page_style_set_id', 'rand_cdf').distinct()
        options = tuple(campaign_page_style_sets.iterator())

        if options:
            # Store in cache
            django.core.cache.cache.set(cache_key, options, settings.PAGE_STYLE_CACHE_TIMEOUT)

    # Assign PageStyles:
    page_style_set_id = utils.random_assign(
        (page_style_set_id, rand_cdf)
        for (_pk, page_style_set_id, rand_cdf) in options
    )

    # Record assignment:
    db.delayed_save.delay(
        models.relational.Assignment.make_managed(
            visit_id=visit.pk,
            campaign_id=campaign.pk,
            content_id=(content and content.pk),
            feature_row=page_style_set_id,
            chosen_from_rows=[pk for (pk, _page_style_set_id, _rand_cdf) in options],
            manager=campaign.campaignpagestylesets,
        )
    )

    cache_key = 'pagestyleset|{}'.format(page_style_set_id)
    hrefs = django.core.cache.cache.get(cache_key)
    if hrefs is None:
        page_style_set = models.relational.PageStyleSet.objects.get(pk=page_style_set_id)
        page_styles = page_style_set.page_styles.only('url')
        hrefs = tuple(page_style.href for page_style in page_styles.iterator())

        django.core.cache.cache.set(cache_key, hrefs, settings.PAGE_STYLE_CACHE_TIMEOUT)

    return hrefs
