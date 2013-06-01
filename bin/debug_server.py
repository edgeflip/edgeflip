#!/usr/bin/env python
from edgeflip.settings import config
import edgeflip.web
app = edgeflip.web.getApp()

app.config['USE_S3_DEBUG'] = True

if __name__ == '__main__':
    app.run(debug=True)

