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
from services.user_service import *
from services.visitor_service import *
from reports import *
from sample import *
from pages import *
from services.map_user_to_visitor_service import *
from services.map_user_to_deployment_service import *
from services.deployment_service import *
from base.basehandler import *

class TaskHandler(BaseHandler):
    def get(self):
        users = User.query().fetch()
        for user in users:
            if user.is_super_admin is None or user.is_super_admin == False:
                if user.deployment_key is None:
                    first_map = MapUserToDeployment.query(MapUserToDeployment.user_key == user.key).get()
                    user.deployment_key = first_map.deployment_key
                    user.put()

class SaveAllMaps(BaseHandler):
    def get(self):
        return []
