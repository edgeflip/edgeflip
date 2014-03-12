import importlib

import django.conf


STATICFILES_APP = None
STATICFILES_APPS = {'staticfiles', 'django.contrib.staticfiles'}

for app in django.conf.settings.INSTALLED_APPS:
    if app in STATICFILES_APPS:
        STATICFILES_APP = app


def load_from_staticfiles(module_path):
    if STATICFILES_APP is None:
        return None

    module_path = module_path if module_path.startswith('.') else '.' + module_path
    return importlib.import_module(module_path, STATICFILES_APP)
