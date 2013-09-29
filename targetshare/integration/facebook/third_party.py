"""Methods for integrating with third-party Facebook data providers"""
import datetime
import HTMLParser

import requests
from django.db import transaction
from django.utils import timezone

from targetshare import models


class FBMetaParser(HTMLParser.HTMLParser):
    """HTML parser to collect Facebook object attributes from meta tags"""

    # meta tags whose "content" is of interest:
    meta_attrs = {
        'property': (
            'og:type',
            'og:title',
            'og:image',
            'og:description',
            'og:site_name',
        )
    }

    def reset(self):
        super(FBMetaParser, self).reset()
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


def get_fbobject_attributes(source_url, fb_object=None):
    """Retrieve Facebook object attributes from the meta tags of the given
    URL's HTML source document.

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

    attrs = {} # TODO: cache me under source_url
    for field in models.relational.FBObjectAttribute._meta.fields:
        meta_name = CUSTOM_ATTRIBUTE_NAMES.get(field.name,
                                               field.name.replace('_', ':'))
        if meta_name in parser.meta:
            attrs[field.name] = parser.meta[meta_name]

    return models.relational.FBObjectAttribute(fb_object=fb_object, **attrs)


def get_campaign_fbobject(campaign, source_url):
    # TODO: docstring
    # Retrieve CampaignFBObject sourced from URL
    campaign_fb_object, _created = campaign.campaignfbobjects.for_datetime().get_or_create(
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
    yesterday = now - datetime.timedelta(days=1)
    if not campaign_fb_object.sourced or campaign_fb_object.sourced <= yesterday:
        raw_fb_attrs = get_fbobject_attributes(campaign_fb_object.source_url, fb_object)
        generic_campaign_fbobject = campaign.campaigngenericfbobjects.for_datetime().get()
        generic_fb_object = generic_campaign_fbobject.fb_object
        default_attrs = generic_fb_object.fbobjectattribute_set.for_datetime().get()
        fb_object.fbobjectattribute_set.source(raw_fb_attrs, default_attrs)
        campaign_fb_object.sourced = timezone.now()
        campaign_fb_object.save()

    return fb_object
