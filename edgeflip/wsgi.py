"""
WSGI config for edgeflip project.

This module contains the WSGI application used by Django's development server
and any production WSGI deployments. It should expose a module-level variable
named ``application``. Django's ``runserver`` and ``runfcgi`` commands discover
this application via the ``WSGI_APPLICATION`` setting.

Usually you will have the standard Django WSGI application here, but it also
might make sense to replace the whole Django WSGI application with a custom one
that later delegates to the Django one. For example, you could introduce WSGI
middleware here, or combine a Django application with an application of another
framework.

"""
import os
import sys

# Activate Python virtual environment:
activate_this = '/var/www/edgeflip/bin/activate_this.py'
if os.path.exists(activate_this):
    execfile(activate_this, dict(__file__=activate_this))

# Set up Django:
# We defer to a DJANGO_SETTINGS_MODULE already in the environment. This breaks
# if running multiple sites in the same mod_wsgi process. To fix this, use
# mod_wsgi daemon mode with each site in its own daemon process, or use
# os.environ["DJANGO_SETTINGS_MODULE"] = "edgeflip.settings"
CURRENT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(CURRENT_PATH, '../')))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "edgeflip.settings")

# Initialize new relic:
from django.conf import settings
if settings.NEWRELIC.enabled:
    import newrelic.agent
    newrelic.agent.initialize(settings.NEWRELIC.inifile,
                              settings.NEWRELIC.environment)

# This application object is used by any WSGI server configured to use this
# file. This includes Django's development server, if the WSGI_APPLICATION
# setting points here.
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

# Apply WSGI middleware here.
if settings.NEWRELIC.enabled:
    application = newrelic.agent.wsgi_application()(application)
