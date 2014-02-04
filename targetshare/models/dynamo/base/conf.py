import os
import re

import yaml


CONF_ENV_VAR = 'FARADAY_SETTINGS_FILE'
CONF_FILE_PATTERN = re.compile(r'^faraday\.ya?ml$')

DEFAULTS = (
    # (internal name, namespaced name, default value)
    ('AWS_ACCESS_KEY_ID', None, None),
    ('AWS_SECRET_ACCESS_KEY', None, None),
    ('ENGINE', 'FARADAY_ENGINE', 'aws'),
    ('MOCK', 'FARADAY_MOCK', 'localhost:4567'),
    ('PREFIX', 'FARADAY_PREFIX', ''),
    ('LOGGER', 'FARADAY_LOGGER', 'faraday'),
)


class ConfigurationError(Exception):
    pass


class ConfigurationLookupError(ConfigurationError, LookupError):
    pass


class ConfigurationValueError(ConfigurationError, ValueError):
    pass


def load():
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

    return {name: getattr(settings, (ns_name or name), default)
            for (name, ns_name, default) in DEFAULTS}


class LazySettings(object):

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
            return super(LazySettings, self).__getattr__(key)

        self.load()
        return getattr(self, key)


settings = LazySettings()
