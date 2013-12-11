from collections import defaultdict

from django.dispatch import Signal


# No need to depend on Django, but as long as we have access to
# their signal/receiver implementation...:
item_declared = Signal(providing_args=["item"])


cache = {}


def populate_cache(sender, **_kws):
    cache[sender.__name__] = sender


pending_links = defaultdict(set)


def resolve_links(sender, **_kws):
    for obj in pending_links.pop(sender.__name__, ()):
        obj.resolve_link(sender)


item_declared.connect(populate_cache)
item_declared.connect(resolve_links)
