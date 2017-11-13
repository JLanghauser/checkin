#!/usr/bin/env python
import cgi
import datetime
import webapp2
from array import *
from base.auth_helpers import *
from google.appengine.ext import ndb
from google.appengine.api import users
from google.appengine.ext.webapp import blobstore_handlers
from random import randint
import unicodedata
from time import sleep
import csv
import StringIO
import json
from reports import *
from sample import *
from pages import *

from base.basehandler import *

class ErrorPage(BaseHandler):

    def get(self):
        auth = self.auth
        self.render_template('error_page.html')
