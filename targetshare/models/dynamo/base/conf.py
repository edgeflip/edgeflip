import os
import re

import yaml


CONF_ENV_VAR = 'FARADAY_SETTINGS_FILE'
CONF_FILE_PATTERN = re.compile(r'^faraday\.ya?ml$')

DEFAULTS = (
    # (internal name, namespaced name, default value)
    ('AWS_ACCESS_KEY_ID', None, None),
    ('AWS_SECRET_ACCESS_KEY', None, None),
    ('DEBUG', 'FARADAY_DEBUG', False),
    ('ENGINE', 'FARADAY_ENGINE', 'aws'),
    ('LOGGER', 'FARADAY_LOGGER', 'faraday'),
    ('MOCK', 'FARADAY_MOCK', 'localhost:4567'),
    ('PREFIX', 'FARADAY_PREFIX', ''),
)


class ConfigurationError(Exception):
    pass


class ConfigurationLookupError(ConfigurationError, LookupError):
    pass


class ConfigurationValueError(ConfigurationError, ValueError):
    pass


def load():
    """Retrieve a configuration dict from YAML or Django settings.

    If a YAML configuration file path is specified in the OS environment, this
    is loaded and returned; otherwise, the current working directory is
    searched for an appropriately-named YAML file.

    Should no YAML configuration be discovered, an attempt is made to load a
    Django settings module, and upon success configuration is generated from it.
    Django settings may be flat, in the form `FARADAY_DEBUG`, or in a namespaced
    dictionary, e.g. `DEBUG` under `FARADAY`, except for `AWS_ACCESS_KEY_ID` and
    `AWS_SECRET_ACCESS_KEY`, which may be namespaced or not.

    If AWS configuration is not specified, it will be retrieved dynamically
    from the OS environment.

    """
    # Check for YAML config specified in environ or found in cwd:
    file_ = os.environ.get(CONF_ENV_VAR)
    if not file_:
        cwd = os.getcwd()
        for node in os.listdir(cwd):
            match = CONF_FILE_PATTERN.search(node)
            if match:
                file_ = os.path.join(cwd, match.group(0))
                break
    if file_:
        return yaml.load(open(file_))

    # Check for config in Django settings:
    try:
        from django.conf import settings
    except ImportError:
        raise ConfigurationLookupError("No configuration found")

    try:
        conf = settings.FARADAY.copy()
    except AttributeError:
        return dict(map_django_settings(settings))

    for aws_key in ('AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY'):
        if aws_key not in conf:
            try:
                conf[aws_key] = getattr(settings, aws_key)
            except AttributeError:
                pass
    return conf


def map_django_settings(settings):
    """Generate internal configuration pairs from the given Django settings
    module.

    """
    for (name, ns_name, _default) in DEFAULTS:
        try:
            value = getattr(settings, (ns_name or name))
        except AttributeError:
            pass
        else:
            yield (name, value)


class LazySettings(object):
    """Object which `load()`s configuration into its dictionary only upon its
    first access.

    """
    def __init__(self):
        self.loaded = False

    def load(self):
        config = load()
        vars(self).update(
            (name, config.get(name, default))
            for (name, _ns_name, default) in DEFAULTS
        )
        self.loaded = True

    def __getattr__(self, key):
        if self.loaded:
            raise AttributeError("'{}' object has no attribute '{}'"
                                 .format(self.__class__.__name__, key))

        self.load()
        return getattr(self, key)


settings = LazySettings()
