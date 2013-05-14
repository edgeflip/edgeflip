activate_this = '/var/www/edgeflip/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

from edgeflip.settings import config

if config.newrelic.enabled:
    import newrelic.agent
    newrelic.agent.initialize(config.newrelic.inifile,
                              config.newrelic.environment)

import edgeflip.web
app = edgeflip.web.getApp()

if config.newrelic.enabled:
    app = newrelic.agent.wsgi_application()(app)