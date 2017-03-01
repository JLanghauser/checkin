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
from datatables import *
from requests import *
from google.appengine.datastore.datastore_query import Cursor
from contextlib import closing
from zipfile import ZipFile, ZIP_DEFLATED
from google.appengine.api import urlfetch
import zipfile
import StringIO
from google.appengine.ext import deferred
from google.appengine.api import taskqueue
from google.appengine.runtime import DeadlineExceededError

class VisitorZipDump(BaseHandler,blobstore_handlers.BlobstoreDownloadHandler):
    def get(self,deployment_slug=None):
        dep = Deployment.get_by_slug(deployment_slug)
        if dep.get_qr_codes_url() != "":
            self.response.headers['Content-Type'] ='application/zip'
            self.response.headers['Content-Disposition'] = 'attachment; filename="data.txt.zip"'
            blob_info = blobstore.BlobInfo.get(dep.qr_codes_zip)
            self.send_blob(blob_info)
            #self.response.out.write(dep.qr_codes_zip)
        else:
            deferred.defer(dep.create_file,None,0)
            self.render_json(['Generating QR code zip now - check back in 2-15 minutes'])

class VisitorSave(webapp2.RequestHandler):
    def post(self):
        key = self.request.get('visitor_key')
        if key:
            visitor_key = ndb.Key(urlsafe=key)
            v = visitor_key.get()
            v.set_qr_code()
            v.put()

class VisitorCSV(BaseHandler):
    @deployment_admin_required
    def get(self,deployment_slug=None):
        dep = Deployment.get_by_slug(deployment_slug)
        visitors = Visitor.query(Visitor.deployment_key==dep.key).order(Visitor.serialized_id).fetch()
        csv = ""
        for v in visitors:
            csv = csv + str(v.serialized_id) + ',' + str(v.visitor_id) + ',' + str(v.checkin_url) +  '\r'
        return self.render_csv(csv,"badge-export.csv")

class VisitorDump(BaseHandler):
    @deployment_admin_required
    def get(self,deployment_slug=None):
        dep = Deployment.get_by_slug(deployment_slug)
        visitors = Visitor.query(Visitor.deployment_key==dep.key).order(Visitor.serialized_id).fetch()
        params = {'visitors': visitors}
        self.render_smart_template('DEPLOYMENT','VISITORS','visitor_dump.html',dep,params)

class VisitorsAsyncHandler(BaseHandler):
    @deployment_admin_required
    def get(self,deployment_slug=None):
        start = self.request.get('start')
        length = self.request.get('length')
        order = self.request.get('order')
        order_column = 0
        order_dir = 'asc'

        if order and order[0] and order[0][column]:
            order_column = int(order[0][column])
        if order and order[0] and order[0][dir]:
            order_dir = order[0][dir]

        start = int(start) if start else 0
        length = int(length) if length else 10 #10,25,50,100

        dep = Deployment.get_by_slug(deployment_slug)
        query = Visitor.query(Visitor.deployment_key==dep.key)
        total = query.count()
        if (order_column == 0):
            if order_dir == 'asc':
                query = query.order(Visitor.serialized_id)
            else:
                query = query.order(-Visitor.serialized_id)
        elif (order_column == 1):
            if order_dir == 'asc':
                query = query.order(Visitor.visitor_id)
            else:
                query = query.order(-Visitor.visitor_id)

        visitors = query.fetch(offset=start,limit=length)
        vser = []
        for v in visitors:
            vser.append([v.serialized_id,v.visitor_id,v.qr_code_url])


        obj = {
            'success': 'true',
            'recordsTotal': total,
            'recordsFiltered':total,
            'data': vser,
          }
        self.render_json(obj)


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
