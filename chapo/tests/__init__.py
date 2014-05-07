from mock import patch


BYTES = '\xad\xe0\xd0\x9a\xf5\xe1\xedz\xe9\xd9\xd2\x8b'
BYTES2 = '\x08A\x1av\xbfH\xfaK{\x1e\xd2n'

urandom_patch = patch('os.urandom', return_value=BYTES)

_settings_patch = patch('django.conf.settings.CELERY_ALWAYS_EAGER', True)


def setup_package():
    _settings_patch.start()


def teardown_package():
    _settings_patch.stop()
