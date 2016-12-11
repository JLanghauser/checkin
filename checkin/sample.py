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

class SampleHandler(BaseHandler):
    def set_sample_qr_code(self,deployment):
        factory = qrcode.image.svg.SvgPathImage
        #img = qrcode.make('Some data here', image_factory=factory)
        #img = qrcode.make(deployment.custom_subdomain
        #             + "."
        #             + deployment.custom_dns
        #             + "/checkin_visitor?visitor_id="
        #             + "9999999", image_factory=PymagingImage)
        # factory = PymagingImage
        # qr = qrcode.QRCode(
        #     version=None,
        #     error_correction=qrcode.constants.ERROR_CORRECT_L,
        #     box_size=100,
        #     border=4,
        # )
        # qr.add_data('Some data')
        # qr.make(fit=True)
        # img = qr.make_image(image_factory=factory)
        #
        #deployment.upload_qr_code(svg,"image/svg")

    def get_deployment_params(self,deployment,**kwargs):
        params = {}
        params['logo_url'] = deployment.logo_url
        params['header_color'] = deployment.header_background_color
        params['footer_text'] =  deployment.footer_text
        for key, value in kwargs.items():
            params[key] = value
        return params

    @user_login_required
    def get(self, deployment_slug=None):
        params = {}
        if deployment_slug:
            dep = Deployment.get_by_slug(deployment_slug)
            params = self.get_deployment_params(dep)

        #   if not dep.sample_qr_code:
            #self.set_sample_qr_code(dep)
            #params['sample_url'] = dep.get_sample_qr_code_url()
            params['sample_url'] = '/img/ri_sample.png'
            visitor = Visitor.query( Visitor.visitor_id == "9999999",
                                     Visitor.deployment_key == dep.key).fetch(1)
            if not visitor or len(visitor) == 0 or not visitor[0]:
                visitor = Visitor()
                visitor.visitor_id = "9999999"
                visitor.deployment_key = dep.key
                visitor.put()
            else:
                visitor = visitor[0]

            vis_map = MapUserToVisitor.query(
                                   MapUserToVisitor.user_key == self.user.key,
                                   MapUserToVisitor.visitor_key == visitor.key,
                                   MapUserToVisitor.deployment_key == dep.key).fetch()

            if vis_map and len(vis_map) > 0 and vis_map[0]:
                params['complete'] = 'true'
            else:
                params['complete'] = 'false'

        self.render_template('sample.html',params)

    @user_login_required
    def post(self, deployment_slug=None):
        params = {}
        if deployment_slug:
            dep = Deployment.get_by_slug(deployment_slug)
            params = self.get_deployment_params(dep)

            params['sample_url'] = '/img/ri_sample.png'
            visitor = Visitor.query( Visitor.visitor_id == "9999999",
                                     Visitor.deployment_key == dep.key).fetch(1)
            if not visitor or len(visitor) == 0 or not visitor[0]:
                visitor = Visitor()
                visitor.visitor_id = "9999999"
                visitor.deployment_key = dep.key
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
