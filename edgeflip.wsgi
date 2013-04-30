activate_this = '/var/www/edgeflip/bin/activate'
execfile(activate_this, dict(__file__=activate_this))

from edgeflip.settings import config

# ideally, the app to run would be determined by config? or uWSGI, hmm...
from edgeflip.ofa_flask import app as application
