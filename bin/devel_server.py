#!/usr/bin/env python

from werkzeug.serving import run_simple
from edgeflip.settings import config
import edgeflip.web
import argparse




parser = argparse.ArgumentParser(description='Run a devel server from localhost')
parser.add_argument('--port', default=8080, type=int, help='force server to run on given port')
args = parser.parse_args()

app = edgeflip.web.getApp()
app.debug = True

run_simple('localhost', args.port, app,
           use_reloader=True,
           use_debugger=True,
           passthrough_errors=False,
           extra_files=config.list_files(), # config files, etc..
           static_files={},
           ssl_context=None
          )
