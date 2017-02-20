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
# import qrcode
# import qrcode.image.svg
# from qrcode.image.pure import PymagingImage
# from base.qrcodegen import *
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
