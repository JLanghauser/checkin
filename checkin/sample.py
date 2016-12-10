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

class SampleHandler(BaseHandler):
    def set_sample_qr_code(self,deployment):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(deployment.custom_subdomain
                    + "."
                    + deployment.custom_dns
                    + "/checkin_visitor?visitor_id="
                    + "9999999")
        qr.make(fit=True)
        img = qr.make_image()
        deployment.upload_qr_code(img)

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

            if not dep.sample_qr_code:
                self.set_sample_qr_code(dep)

            params['sample_url'] = dep.get_sample_qr_code_url()


        self.render_template('sample.html',params)

    @user_login_required
    def post(self, deployment_slug=None):
        self.render_template('reports.html',params)
