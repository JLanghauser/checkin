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
from google.appengine.api import images
from services.deployment_service import *
from services.visitor_service import *

class SampleHandler(BaseHandler):

    def get_deployment_params(self,deployment,**kwargs):
        params = {}
        params['slug'] = deployment.slug
        params['logo_url'] = deployment.logo_url
        params['header_color'] = deployment.header_background_color
        params['footer_text'] =  deployment.footer_text
        for key, value in kwargs.items():
            params[key] = value
        return params

    def get(self, deployment_slug=None):
        params = {}
        if deployment_slug:
            dep = Deployment.get_by_slug(deployment_slug)
            params = self.get_deployment_params(dep)

        #   if not dep.sample_qr_code:
            #self.set_sample_qr_code(dep)
            #params['sample_url'] = dep.get_sample_qr_code_url()
            #params['sample_url'] = '/img/ri_sample.png'
            params['sample_url'] = dep.get_sample_qr_code_url()
            visitor = Visitor.query( Visitor.visitor_id == "9999999",
                                     Visitor.deployment_key == dep.key).fetch(1)
            if not visitor or len(visitor) == 0 or not visitor[0]:
                visitor = Visitor()
                visitor.visitor_id = "9999999"
                visitor.deployment_key = dep.key
                VisitorService.set_qr_code(visitor)
                visitor.put()
            else:
                visitor = visitor[0]

            # vis_map = MapUserToVisitor.query(
            #                        MapUserToVisitor.user_key == self.user.key,
            #                        MapUserToVisitor.visitor_key == visitor.key,
            #                        MapUserToVisitor.deployment_key == dep.key).fetch()
            #
            # if vis_map and len(vis_map) > 0 and vis_map[0]:
            #     params['complete'] = 'true'
            # else:
            params['complete'] = 'false'

        self.render_template('sample.html',params)

    @user_login_required
    def post(self, deployment_slug=None):
        params = {}
        if deployment_slug:
            dep = Deployment.get_by_slug(deployment_slug)
            params = self.get_deployment_params(dep)

            if (dep.sample_qr_code):
                params['sample_url'] = images.get_serving_url(dep.sample_qr_code,300,False,True)
            else:
                params['sample_url'] = ""

            visitor = Visitor.query( Visitor.visitor_id == "9999999",
                                     Visitor.deployment_key == dep.key).fetch(1)
            if not visitor or len(visitor) == 0 or not visitor[0]:
                visitor = Visitor()
                visitor.visitor_id = "9999999"
                visitor.deployment_key = dep.key
                VisitorService.set_qr_code(visitor)
                visitor.put()
            else:
                visitor = visitor[0]

            vis_map = MapUserToVisitor.query(
                                   MapUserToVisitor.user_key == self.user.key,
                                   MapUserToVisitor.visitor_key == visitor.key,
                                   MapUserToVisitor.deployment_key == dep.key).fetch()

            if vis_map and len(vis_map) > 0 and vis_map[0]:
                vis_map[0].key.delete()
            else:
                params['complete'] = 'false'

        self.render_template('sample.html',params)
