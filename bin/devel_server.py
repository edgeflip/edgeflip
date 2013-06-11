#!/usr/bin/env python

from werkzeug.serving import run_simple
from OpenSSL import SSL
import argparse
import os
from edgeflip.settings import config
import edgeflip.web


# default location for cert files is ../ssl relative to this file
pathBin = os.path.dirname(os.path.realpath(__file__))
pathBase = os.path.dirname(os.path.normpath(pathBin))
pathCertDefault = os.path.join(pathBase, 'ssl')

parser = argparse.ArgumentParser(description='Run a devel server from localhost')
parser.add_argument('--canvas', action='store_true', help='fb canvas mode (ssl, port 443)')
parser.add_argument('--cert-dir', default=pathCertDefault, help='location of ssl and cert files, defaults to ../ssl/')
parser.add_argument('--ssl-key', default='ssl.key', help='name of ssl key file, defaults to ssl.key')
parser.add_argument('--ssl-cert', default='ssl.cert', help='name of ssl cert file, defaults to ssl.cert')
parser.add_argument('--canvas-adhoc', action='store_true', help='fb canvas mode with adhoc cert (no key/cert files)')
args = parser.parse_args()

app = edgeflip.web.getApp()
app.debug = True

# if we're testing the FB canvas app, we need to run with SSL on port 443 (must run with sudo!)
if (args.canvas) or (args.canvas_adhoc):
    port = 443

    # Two choices here for dealing with certs:
    #
    # (A) Create a self-signed cert (following http://werkzeug.pocoo.org/docs/serving/#ssl)
    #         $ openssl genrsa 1024 > ssl.key
    #         $ openssl req -new -x509 -nodes -sha1 -days 365 -key ssl.key > ssl.cert
    # using those files, create a cert object
    if (args.canvas):
        pathKey = os.path.join(args.cert_dir, args.ssl_key)
        pathCert = os.path.join(args.cert_dir, args.ssl_cert)
        ctx = SSL.Context(SSL.SSLv23_METHOD)
        ctx.use_privatekey_file(pathKey)
        ctx.use_certificate_file(pathCert)

    # (B) Otherwise, you can go with ad hoc mode, however, you must accept the cert in a browser
    #     before making the request via FB app page (e.g., go to https://app.edgeflip.com/canvas/,
    #     and click okay before hitting https://apps.facebook.com/sharing-social-good/)
    else:
        ctx = 'adhoc'

# otherwise, we're rocking port 8080
else:
    port = 8080
    ctx = None

run_simple('localhost', port, app,
           use_reloader=True,
           use_debugger=True,
           passthrough_errors=False,
           extra_files=config.list_files(), # config files, etc..
           static_files={},
           ssl_context=ctx
          )
