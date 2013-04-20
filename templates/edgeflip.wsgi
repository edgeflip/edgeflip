activate_this = '$VIRTUALENV_PATH/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

from edgeflip.settings import config

# ideally, the app to run would be determined by config? or uWSGI, hmm...
from edgeflip.ofa_flask import app as application
