#!/usr/bin/env python
"""upload files to the s3 bucket specified in configuration"""

import flask_s3

from edgeflip.settings import config
import edgeflip.web
app = edgeflip.web.getApp()

flask_s3.create_all(app)