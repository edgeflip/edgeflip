activate_this = '$VIRTUALENV_PATH/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

from edgeflip.ofa_flask import app as application
