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
from models.user import *
from models.deployment import *
from reports import *
from sample import *
from pages import *
from models.map_user_to_visitor import *
from models.deployment import *

from base.basehandler import *

class TaskHandler(BaseHandler):
    def get(self):
        return []
