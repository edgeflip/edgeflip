from django.dispatch import Signal


# No need to depend on Django, but as long as we have access to
# their signal/receiver implementation...:
item_declared = Signal(providing_args=["item"])


cache = {}


def populate_cache(sender, **_kws):
    cache[sender.__name__] = sender

item_declared.connect(populate_cache)
