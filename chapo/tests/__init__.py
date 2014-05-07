import pymlconf
from django.core import cache
from mock import patch


BYTES = '\xad\xe0\xd0\x9a\xf5\xe1\xedz\xe9\xd9\xd2\x8b' # => jSgnUTqptPrV
BYTES2 = '\x08A\x1av\xbfH\xfaK{\x1e\xd2n' # => WSTUhHUshgrt

urandom_patch = patch('os.urandom', return_value=BYTES)


_settings_patch = patch.multiple('django.conf.settings',
    CACHES=pymlconf.ConfigDict({
        'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}
    }),
    CELERY_ALWAYS_EAGER=True,
)


def setup_package():
    _settings_patch.start()
    reload(cache)


def teardown_package():
    _settings_patch.stop()
    reload(cache)
