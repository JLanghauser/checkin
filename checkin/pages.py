#!/usr/bin/env python
import webapp2
from models import *
import cgi
import datetime
import webapp2
from array import *
from basehandler import *
from auth_helpers import *
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
import qrcode
import qrcode.image.svg
from qrcode.image.pure import PymagingImage
from qrcodegen import *

class InstructionsHandler(BaseHandler):
    def get_deployment_params(self,deployment,**kwargs):
        params = {}
        params['slug'] = deployment.slug
        params['logo_url'] = deployment.logo_url
        params['header_color'] = deployment.header_background_color
        params['footer_text'] =  deployment.footer_text
        for key, value in kwargs.items():
            params[key] = value
        return params

    @deployment_admin_required
    def get(self, deployment_slug=None):
        params = {}
        if deployment_slug:
            dep = Deployment.get_by_slug(deployment_slug)
            params = self.get_deployment_params(dep)
        self.render_template('instructions.html',params)
