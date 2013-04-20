#!/usr/bin/env python

from werkzeug.serving import run_simple
from edgeflip.settings import config

# ideally, the app to run would be determined by config? or uWSGI, hmm...
from edgeflip.ofa_flask import app

app.debug = True

run_simple('localhost', 8080, app,
           use_reloader=True,
           use_debugger=True,
           passthrough_errors=False,
           extra_files=config.list_files(), # config files, etc..
           static_files={},
          )
