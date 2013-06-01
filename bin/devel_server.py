#!/usr/bin/env python

from werkzeug.serving import run_simple
from edgeflip.settings import config
import edgeflip.web
app = edgeflip.web.getApp()

app.debug = True

app.config['USE_S3_DEBUG'] = True

run_simple('localhost', 8080, app,
           use_reloader=True,
           use_debugger=True,
           passthrough_errors=False,
           extra_files=config.list_files(), # config files, etc..
           static_files={},
          )
