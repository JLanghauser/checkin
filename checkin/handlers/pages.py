#!/usr/bin/env python
import webapp2
import cgi
import datetime
import webapp2
from array import *
from base.basehandler import *
from base.auth_helpers import *
from google.appengine.ext import ndb
from google.appengine.api import users
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.api import images
from google.appengine.ext import db, ndb, blobstore
from random import randint
import unicodedata
from time import sleep
import csv
import StringIO
import json
import sys
from google.appengine.ext import deferred
from google.appengine.api import taskqueue
from google.appengine.runtime import DeadlineExceededError
from models.map_user_to_visitor import *
from models.deployment import *

class InstructionsHandler(BaseHandler):
    @deployment_admin_required
    def get(self, deployment_slug=None):
        params = {}
        if deployment_slug:
            dep = Deployment.get_by_slug(deployment_slug)
            params = self.add_deployment_params({},dep)
        self.render_template('instructions.html',params)

class MainPage(BaseHandler):
    def get(self, deployment_slug=None):
        user = self.user
        dep = None
        if deployment_slug:
            dep = Deployment.query(Deployment.slug == deployment_slug).fetch(1)
            if dep and len(dep) > 0:
                dep = dep[0]
            else:
                dep = None

        if (user):
            if dep:
                params = self.get_params_hash(
                    self.add_deployment_params({},dep,userprofile=user.profile))
            else:
                params = self.get_params_hash({},userprofile=user.profile)
            self.render_template('index.html', params)
        else:
            if dep:
                params = self.get_params_hash(self.add_deployment_params({},dep))
            else:
                params = {}
            self.render_template('index.html', params)

class UploadHandler(blobstore_handlers.BlobstoreUploadHandler):
    def post(self):
        try:
            upload = self.get_uploads()[0]
            self.response.headers['Content-Type'] = 'application/json'
            obj = {'success': 'true', 'key': str(upload.key()), }
            self.response.out.write(json.dumps(obj))
        except:
            self.error(500)

class CreateVisitors(BaseHandler):
    @classmethod
    def create_if_does_not_exist(cls,offset):
        next_offset = offset
        try:
            maps = MapUserToVisitor.query().order(MapUserToVisitor.visitor_key).fetch(offset=next_offset)
            for m in maps:
                visitor = m.visitor_key.get()
                if not visitor:
                    v = Visitor(id = m.visitor_key.id())
                    if m.deployment_key:
                        v.deployment_key = m.deployment_key
                    v.put()
                next_offset = next_offset + 1

        except DeadlineExceededError:
            deferred.defer(CreateVisitors.create_if_does_not_exist,next_offset)

    def get(self):
        deferred.defer(CreateVisitors.create_if_does_not_exist,0)
        return []

class DebugHandler(BaseHandler):
    def get(self):
        maps = MapUserToVisitor.query().order(MapUserToVisitor.deployment_key,MapUserToVisitor.visitor_key)

        csv = "deployment_key_id,visitor_key_id\r"
        for m in maps:
            csv = csv + str(m.deployment_key.id()) + ',' + str(m.visitor_key.id()) + '\r'

        self.render_csv(csv,'maps.csv')
