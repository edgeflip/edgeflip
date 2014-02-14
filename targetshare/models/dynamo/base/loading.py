import collections

import dispatch

from . import conf, utils


class Signal(dispatch.Signal):

    @utils.class_property
    def debug(_cls):
        return conf.settings.DEBUG


item_declared = Signal(providing_args=["item"])


cache = {}


def populate_cache(sender, **_kws):
    cache[sender._meta.signed] = sender


pending_links = collections.defaultdict(set)


def resolve_links(sender, **_kws):
    for obj in pending_links.pop(sender._meta.signed, ()):
        obj.resolve_link(sender)


item_declared.connect(populate_cache)
item_declared.connect(resolve_links)
