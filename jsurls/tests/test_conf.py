import django.conf
from django.core.exceptions import ImproperlyConfigured

from jsurls import conf


# Configure Django settings for tests without any customization:
try:
    django.conf.settings.configure(
        DATABASES={ # (not that we'll use any of this)
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': 'jsurls.db',
            },
        },
    )
except RuntimeError:
    # settings already configured
    # TODO: remove this once project split out
    CLEAR_SETTINGS = []
    for (key, _value) in conf.GLOBAL_DEFAULTS:
        djkey = 'JSURLS_' + key
        try:
            value = getattr(django.conf.settings, djkey)
        except AttributeError:
            pass
        else:
            CLEAR_SETTINGS.append((djkey, value))
else:
    CLEAR_SETTINGS = ()


def setup_module():
    for (key, _value) in CLEAR_SETTINGS:
        delattr(django.conf.settings, key)


def teardown_module():
    for (key, value) in CLEAR_SETTINGS:
        setattr(django.conf.settings, key, value)


# Now safe to import from django.test:
from django.test import SimpleTestCase
from django.test.utils import override_settings


def djsettings(**config):
    config_prefixed = {'JSURLS_' + key: value for (key, value) in config.iteritems()}
    return override_settings(**config_prefixed)


class TestProfile(SimpleTestCase):

    def test_defaults(self):
        profile = conf.Profile()
        self.assertEqual(profile.INSTALL_PATH, None)
        self.assertEqual(profile.JS_NAMESPACE, 'router')
        self.assertEqual(profile.URL_INCLUDES, set())
        self.assertEqual(profile.URL_EXCLUDES, set())
        self.assertEqual(profile.URL_NAMESPACES, set())

    def test_set_bad_key(self):
        with self.assertRaises(TypeError):
            conf.Profile(INSTALL_LAUGH='~')

    def test_set_bad_value(self):
        with self.assertRaises(ImproperlyConfigured):
            conf.Profile(URL_NAMESPACES=object())

    def test_sequence_single_value(self):
        profile = conf.Profile(URL_INCLUDES='admin')
        self.assertEqual(profile.URL_INCLUDES, {'admin'})

    def test_set(self):
        path = '/var/www/router.js'
        profile = conf.Profile(INSTALL_PATH=path)
        self.assertEqual(profile.INSTALL_PATH, path)
        self.assertEqual(profile.JS_NAMESPACE, 'router')

    def test_fallback(self):
        path = '/var/www/router.js'
        fallback = type('Settings', (), {'JS_NAMESPACE': 'namespace.module', 'URL_INCLUDES': ['^mock/']})
        profile = conf.Profile(fallback, INSTALL_PATH=path)
        self.assertEqual(profile.INSTALL_PATH, path)
        self.assertEqual(profile.JS_NAMESPACE, 'namespace.module')
        self.assertEqual(profile.URL_INCLUDES, {'^mock/'})
        self.assertEqual(profile.URL_NAMESPACES, set())

    def test_fallback_merge(self):
        fallback = type('Settings', (), {'URL_INCLUDES': ['^mock/']})
        profile = conf.Profile(fallback, URL_INCLUDES=['^birds/'])
        self.assertEqual(profile.URL_INCLUDES, {'^birds/', '^mock/'})
        self.assertEqual(profile.URL_NAMESPACES, set())


class TestGlobalSettings(SimpleTestCase):

    def test_defaults(self):
        self.assertEqual(conf.settings.INSTALL_PATH, None)
        self.assertEqual(conf.settings.JS_NAMESPACE, 'router')
        self.assertEqual(conf.settings.URL_INCLUDES, set())
        self.assertEqual(conf.settings.URL_EXCLUDES, set())
        self.assertEqual(conf.settings.URL_NAMESPACES, set())
        self.assertEqual(conf.settings.DEBUG_URL, '/jsurls/')
        self.assertEqual(conf.settings.USE_DEBUG_URL, False)
        self.assertEqual(conf.settings.PROFILES, {})

    @djsettings(INSTALL_PATH='/var/www/router.js')
    def test_set(self):
        self.assertEqual(conf.settings.INSTALL_PATH, '/var/www/router.js')

    @djsettings(URL_INCLUDES=object())
    def test_set_bad_value(self):
        with self.assertRaises(ImproperlyConfigured):
            conf.settings.URL_INCLUDES

    @djsettings(URL_INCLUDES='^admin/')
    def test_sequence_single_value(self):
        self.assertEqual(conf.settings.URL_INCLUDES, {'^admin/'})

    @djsettings(JS_NAMESPACE='namespace.module', URL_INCLUDES=['^mock/'])
    def test_override(self):
        self.assertEqual(conf.settings.JS_NAMESPACE, 'namespace.module')
        self.assertEqual(conf.settings.URL_INCLUDES, {'^mock/'})


class TestSettingsProfiles(SimpleTestCase):

    @djsettings(PROFILES=())
    def test_bad_struct(self):
        with self.assertRaises(ImproperlyConfigured):
            conf.settings.PROFILES

    @djsettings(PROFILES={'admin': {'INSTALL_PATH': '/var/www/router.js'}})
    def test_set(self):
        self.assertEqual(conf.settings.INSTALL_PATH, None)
        self.assertEqual(conf.settings.JS_NAMESPACE, 'router')
        profile = conf.settings.PROFILES['admin']
        self.assertEqual(profile.INSTALL_PATH, '/var/www/router.js')
        self.assertEqual(profile.JS_NAMESPACE, 'router')

    @djsettings(PROFILES={'admin': {'JS_NAMESPACE': 'namespace.module'}})
    def test_override(self):
        self.assertEqual(conf.settings.JS_NAMESPACE, 'router')
        profile = conf.settings.PROFILES['admin']
        self.assertEqual(profile.INSTALL_PATH, None)
        self.assertEqual(profile.JS_NAMESPACE, 'namespace.module')

    @djsettings(PROFILES={'admin': {'URL_NAMESPACES': 'admin'}}, URL_NAMESPACES='core')
    def test_merge(self):
        profile = conf.settings.PROFILES['admin']
        self.assertEqual(conf.settings.URL_NAMESPACES, {'core'})
        self.assertEqual(profile.URL_NAMESPACES, {'core', 'admin'})

    @djsettings(PROFILES={'admin': conf.Profile(URL_NAMESPACES='admin')}, URL_NAMESPACES='core')
    def test_merge_profile(self):
        profile = conf.settings.PROFILES['admin']
        self.assertEqual(conf.settings.URL_NAMESPACES, {'core'})
        self.assertEqual(profile.URL_NAMESPACES, {'core', 'admin'})
        self.assertEqual(profile.JS_NAMESPACE, 'router')
