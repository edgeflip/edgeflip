#!/usr/bin/env python

from werkzeug.serving import run_simple
from edgeflip.ofa_flask import app



app.debug=True

run_simple('localhost', 8080, app,
           use_reloader=True,
           use_debugger=True,
           passthrough_errors=False,
           extra_files=[], # config files, etc..
           static_files={},
          )
