#!/usr/bin/env python
# -*- coding: utf-8 -*-

###
### Example application for Google App Engine
###
### Before trying this example, copy 'tenjin.py' to 'lib' folder.
###
###     $ mkdir lib
###     $ cp ../../lib2/tenjin.py lib
###

from __future__ import with_statement

import sys, os
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

is_dev = (os.environ.get("SERVER_SOFTWARE") or "").startswith("Devel")

##
## import tenjin module and helper functions
##
sys.path.insert(0, "lib")        # necessary to import library under 'lib'
import tenjin
#tenjin.set_template_encoding("utf-8")            # if you like
from tenjin import *
from tenjin.helpers import *
from tenjin.helpers.html import *
import tenjin.gae; tenjin.gae.init()              # DON'T FORGET THIS LINE!

##
## engine object
##
tenjin_config = {
    "path":   ["templates"],
    "layout": "_layout.pyhtml",
}
engine = tenjin.Engine(**tenjin_config)
#engine = tenjin.SafeEngine(**tenjin_config)      # if you like

##
## logger
##
import logging
logger = logging.getLogger()
if is_dev:
    logger.setLevel(logging.DEBUG)
tenjin.logger = logger                            # set tenjin logger

##
## handler class
##
class MainHandler(webapp.RequestHandler):
    def get(self):
        context = { "page_title": "Tenjin Example in Google App Engine",
                    "environ": self.request.environ }
        html = engine.render("index.pyhtml", context)
        self.response.out.write(html)

##
## WSGI application
##
mappings = [
    ("/", MainHandler),
]

def main():
    app = webapp.WSGIApplication(mappings, debug=is_dev)
    util.run_wsgi_app(app)


if __name__ == "__main__":
    main()
