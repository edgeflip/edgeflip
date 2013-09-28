"""Methods for integrating with third-party Facebook data providers"""
import HTMLParser

import requests

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


def get_fbobject_attributes(campaign_fb_object):
    """Retrieve Facebook object attributes from the meta tags of the given
    CampaignFBObject's HTML source document.

    """
    try:
        response = requests.get(campaign_fb_object.source_url)
    except requests.exceptions.RequestException as exc:
        raise RetrievalError(exc)

    if not response.ok:
        raise RetrievalError("Resource responded with status code {}: {}"
                             .format(response.status_code, campaign_fb_object.source_url))

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

    return models.relational.FBObjectAttribute(fb_object=campaign_fb_object.fb_object, **attrs)
