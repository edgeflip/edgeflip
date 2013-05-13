activate_this = '/var/www/edgeflip/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

from edgeflip.settings import config
import edgeflip.web
app = edgeflip.web.getApp()
