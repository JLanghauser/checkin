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

class StudentHandler(BaseHandler):
    def get_deployment_params(self,deployment):
        params = {}
        params['logo_url'] = deployment.logo_url
        params['header_color'] = deployment.header_background_color
        params['footer_text'] =  deployment.footer_text
        params['student_link'] =  deployment.student_link
        params['student_link_text'] =  deployment.student_link_text
        return params

    def handlerequest(self, deployment_slug=None):
        visitor_id = self.request.get('visitor_id', '').strip()

        if (visitor_id == '' or not deployment_slug):
            self.render_template('error_page.html')
        else:
            deployment = Deployment.get_by_slug(deployment_slug)

            if not deployment:
                self.render_template('error_page.html')

            params = self.get_deployment_params(deployment)

            qry = Visitor.query(Visitor.visitor_id == visitor_id,
                                Visitor.deployment_key == deployment.key)
            visitor = qry.get()

            if (visitor):
                vkey = visitor.key
                maps = MapUserToVisitor.query(
                    MapUserToVisitor.visitor_key == vkey,
                    MapUserToVisitor.deployment_key == deployment.key).fetch()
                profiles = []
                for map_item in maps:
                    ukey = map_item.user_key
                    u = ukey.get()

                    if ( not u.profile
                         or ("<h1>Edit your profile" in u.profile
                         and ">here</a></h1>" in u.profile
                         and len(u.profile) < 60)):
                        profiles.append("<h2>" + u.vendorname + "</h2>" +
                                        "<h3>This organization hasn't included any information)</h3>")
                    else:
                        profiles.append(
                            "<h2>" + u.vendorname + "</h2>" + u.profile)

                params['profiles'] = profiles
                self.render_template('student.html', params)
            else:
                params['error'] = "true"
                params['flash_message'] = "No such student " + visitor_id
                self.render_template('studentlogin.html', params)

    def get(self,deployment_slug=None):
        visitor_id = self.request.get('visitor_id', '')
        if (visitor_id == ''):
            dep = Deployment.get_by_slug(deployment_slug)
            if dep:
                self.render_template('studentlogin.html',self.get_params_hash(self.get_deployment_params(dep)))
            else:
                self.render_template('studentlogin.html')
        else:
            self.handlerequest(deployment_slug)

    def post(self,deployment_slug=None):
        self.handlerequest(deployment_slug)
