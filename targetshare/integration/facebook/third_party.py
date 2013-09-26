from HTMLParser import HTMLParser

import requests


class FBMetaParser(HTMLParser):

    meta_attrs = {
        'property': (
            'fb:app_id',
            # TODO: ...
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


def get_fbobject_meta(url):
    # TODO: exceptions?
    response = requests.get(url)
    if response.ok:
        parser = FBMetaParser()
        parser.feed(response.text)
        return parser.meta
    else:
        # TODO
        pass
