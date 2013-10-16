"""Methods for integrating with third-party Facebook data providers"""
import datetime
import HTMLParser

import requests
from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone

from targetshare import models


class FBMetaParser(HTMLParser.HTMLParser):
    """HTML parser to collect Facebook object attributes from meta tags"""

    # meta tags whose "content" is of interest:
    meta_attrs = {
        'property': (
            'og:title',
            'og:image',
            'og:description',
            'og:site_name',
        )
    }

    def reset(self):
        HTMLParser.HTMLParser.reset(self)
        self.meta = {}

    def handle_starttag(self, tag, attrs):
        if tag != 'meta':
            return

        attr_dict = dict(attrs)
        try:
            content = attr_dict.pop('content')
        except KeyError:
            return

        for attr_name, attr_value in attr_dict.items():
            if attr_value in self.meta_attrs.get(attr_name, ()):
                self.meta[attr_value] = content


class RetrievalError(Exception):
    pass


class RetrievalParseError(RetrievalError):
    pass


CUSTOM_ATTRIBUTE_NAMES = {
    'org_name': 'og:site_name',
}


def _retrieve_fbobject_meta(source_url):
    """Return the Facebook object attributes specified by the <meta> tags of the HTML
    document at `source_url`.

    Returns: a dict of raw Facebook object attributes

    """
    try:
        response = requests.get(source_url)
    except requests.exceptions.RequestException as exc:
        raise RetrievalError(exc)

    if not response.ok:
        raise RetrievalError("Resource responded with status code {}: {}"
                            .format(response.status_code, source_url))

    parser = FBMetaParser()
    try:
        parser.feed(response.text)
    except HTMLParser.HTMLParseError as exc:
        raise RetrievalParseError(exc)
    else:
        return parser.meta


def get_fbobject_attributes(source_url, fb_object=None, refresh=False):
    """Retrieve Facebook object attributes from the meta tags of the given
    URL's HTML source document.

    Note: Relevant source document meta tags are cached according to
    `retrieval_cache_timeout` (see `settings.CLIENT_FBOBJECT`). To force the cache
    to refresh, specify `refresh`.

    Returns: a ready-to-save FBObjectAttribute object

    """
    cache_key = 'fbobject|{}'.format(source_url)
    meta = refresh or cache.get(cache_key)
    if refresh or meta is None:
        meta = _retrieve_fbobject_meta(source_url)
        cache.set(cache_key, meta, settings.CLIENT_FBOBJECT['retrieval_cache_timeout'])

    attrs = {}
    for field in models.relational.FBObjectAttribute._meta.fields:
        meta_name = CUSTOM_ATTRIBUTE_NAMES.get(field.name,
                                               field.name.replace('_', ':'))
        try:
            attrs[field.name] = meta[meta_name]
        except KeyError:
            pass

    return models.relational.FBObjectAttribute(fb_object=fb_object, **attrs)


def source_campaign_fbobject(campaign, source_url, refresh=False):
    """For a given Campaign and client Facebook object source URL, ensure the existence
    of an active CampaignFBObject, FBObject and FBObjectAttribute.

    FBObject attributes are gathered from the <meta> tags of the HTML document at
    `source_url`, either for a new Campaign FBObject or for that which has not been
    updated within `campaign_max_age` (see `settings.CLIENT_FBOBJECT`). To force
    refresh attributes regardless of how recently they have been sourced, specify
    `refresh`.

    Any attributes missing from `source_url`'s document but present in the
    CampaignGenericFBObject will be populated from the latter.

    On update, invalidated FBObjectAttributes are made inactive by setting `end_dt`.

    Note: this method makes use of a managed transaction, and as such expects to be called
    from a scope in autocommit mode, or which will not be affected by its transaction
    being committed.

    Returns: the Campaign FBObject populated from `source_url`

    """
    # Retrieve CampaignFBObject sourced from URL
    campaign_fb_object, _created = models.CampaignFBObject.objects.for_datetime().get_or_create(
        campaign=campaign,
        source_url=source_url,
    )
    if campaign_fb_object.fb_object is None:
        # Created or created by competing by thread;
        # safely update CampaignFBObject with new FBObject
        with transaction.commit_on_success():
            # Block row from competitors with FOR UPDATE:
            campaign_fb_object = models.CampaignFBObject.objects.select_for_update().get(
                pk=campaign_fb_object.pk
            )
            if campaign_fb_object.fb_object is None:
                # Let winner fill in FBObject
                campaign_fb_object.fb_object = campaign.client.fbobjects.create()
                campaign_fb_object.save()

    fb_object = campaign_fb_object.fb_object

    # (Re)-retrieve FBObjectAttributes from URL (if haven't recently)
    now = timezone.now()
    too_old = now - datetime.timedelta(seconds=settings.CLIENT_FBOBJECT['campaign_max_age'])
    if refresh or not campaign_fb_object.sourced or campaign_fb_object.sourced <= too_old:
        raw_fb_attrs = get_fbobject_attributes(campaign_fb_object.source_url, fb_object, refresh)
        generic_campaign_fbobject = campaign.campaigngenericfbobjects.for_datetime().get()
        generic_fb_object = generic_campaign_fbobject.fb_object
        default_attrs = generic_fb_object.fbobjectattribute_set.for_datetime().get()
        fb_object.fbobjectattribute_set.source(raw_fb_attrs, default_attrs)
        campaign_fb_object.sourced = timezone.now()
        campaign_fb_object.save()

    return fb_object
