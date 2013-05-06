#!/usr/bin/env python
from edgeflip.settings import config
import edgeflip.web
app = edgeflip.web.getApp()

if __name__ == '__main__':
    app.run(debug=True)

