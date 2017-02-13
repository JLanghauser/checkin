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

class VisitorsHandler(BaseHandler):
    def get_deployment_params(self,deployment):
        params = {}
        params['logo_url'] = deployment.logo_url
        params['header_color'] = deployment.header_background_color
        params['footer_text'] =  deployment.footer_text
        params['selected_deployment_slug'] = deployment.slug
        return params

    def add_bulk_visitors(self,user,deployment,bulk_file):
        bgjob = BackgroundJob()
        bgjob.user_key = user.key
        bgjob.deployment_key = deployment.key
        bgjob.job_type = "BULK_VISITOR_ADD"
        bgjob.status = "STARTED"
        bgjob.put()

        reader = None
        try:
            reader = self.get_csv_reader(bulk_file,False)
            count = 0
            for row in reader:
                retval = self.add_visitor(row[0],deployment)
                if retval is not "":
                    params = {'error': "true",'flash_message': retval}
                    if deployment:
                        params['logo_url'] = deployment.logo_url
                        params['logo_url'] = deployment.logo_url
                        params['header_color'] = deployment.header_background_color
                        params['footer_text'] =  deployment.footer_text

                    self.render_template('visitors_index.html', params)
                    return
                else:
                    count = count + 1

            if deployment:
                params = {'success': "true",
                      'flash_message': "Successfully added "
                           + str(count) + " visitors."}

                params['header_color'] = deployment.header_background_color
                params['logo_url'] = deployment.logo_url
                params['footer_text'] =  deployment.footer_text
            else:
                params = {'success': "true",
                      'flash_message': "Successfully added "
                           + str(count) + " visitors."}

            self.render_template('visitors_index.html', params)
            return
        except csv.Error as e:
            if reader:
                params = {'users': users, 'error': "true",
                          'flash_message': "File Error - line %d: %s" % (reader.line_num, e)}
            else:
                params = {'users': users, 'error': "true",
                          'flash_message': "Please verify file format - standard CSV with a header row."}
            self.render_template('visitors_index.html', params)

    def add_visitor(self,visitor_id,deployment=None):
        if deployment:
            qry = Visitor.query(Visitor.visitor_id == visitor_id,
                                Visitor.deployment_key == deployment.key)
        else:
            qry = Visitor.query(Visitor.visitor_id == visitor_id)

        visitor = qry.get()
        if (visitor is None and visitor_id != 9999999):
            newvisitor = Visitor()
            newvisitor.visitor_id = visitor_id
            if deployment:
                newvisitor.deployment_key = deployment.key
            newvisitor.put()
            return ""
        else:
            return "Error - Visitor " + visitor_id + " already exists."

    def handlerequest(self,deployment_slug=None,bulk_file=None):
        visitor_id = self.request.get('visitor_id')
        deployment = Deployment.get_by_slug(deployment_slug)

        if bulk_file:
            return
        else:
            retval = self.add_visitor(visitor_id=visitor_id,
                                      deployment=deployment)
            if retval == "":
                params = {'success': "true",
                          'flash_message': "Successfully created Visitor:  " + visitor_id}
            else:
                params = {'error': "true", 'flash_message': retval}

            if deployment:
                params["logo_url"] = deployment.logo_url
                params['header_color'] = deployment.header_background_color
                params['footer_text'] =  deployment.footer_text

            self.render_template('visitors_index.html', params)

    @deployment_admin_required
    def get(self,deployment_slug=None):
        visitor_id = self.request.get('visitor_id', -1)
        if (visitor_id == -1):
            dep = Deployment.get_by_slug(deployment_slug)

            if dep:
                self.render_template('visitors_index.html',
                            self.get_params_hash(self.get_deployment_params(dep)))
            else:
                self.render_template('visitors_index.html')
        else:
            self.handlerequest(deployment_slug)

    @deployment_admin_required
    def post(self,deployment_slug=None):
        bulk_file = self.request.get('bulkfile', None)
        self.handlerequest(deployment_slug,bulk_file)
