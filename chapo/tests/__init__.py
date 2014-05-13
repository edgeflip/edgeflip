import pymlconf
from django.core import cache
from mock import patch


BYTES = '\xad\xe0\xd0\x9a\xf5\xe1\xedz\xe9\xd9\xd2\x8b' # => jSgnUTqptPrV
BYTES2 = '\x08A\x1av\xbfH\xfaK{\x1e\xd2n' # => WSTUhHUshgrt

urandom_patch = patch('os.urandom', return_value=BYTES)


_settings_patches = (
    patch.multiple(
        'django.conf.settings',
        CACHES=pymlconf.ConfigDict({
            'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}
        }),
    ),
    patch.multiple(
        'django.conf.settings', create=True,
        CELERY_ALWAYS_EAGER=True,
    ),
)


def setup_package():
    for patch_ in _settings_patches:
        patch_.start()
    reload(cache)


def teardown_package():
    for patch_ in _settings_patches:
        patch_.stop()
    reload(cache)
