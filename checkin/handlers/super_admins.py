#!/usr/bin/env python
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
from services.deployment_service import *
from google.appengine.ext import deferred
from services.map_user_to_deployment_service import *

class SuperAdminHandler(BaseHandler):
    def delete_booth(self):
        name = self.request.get('name')
        slug = self.request.get('slug')

    def create_new_deployment(self):
        name = self.request.get('name')
        slug = self.request.get('slug')

        existing_deployment = Deployment.get_by_slug(slug)

        if existing_deployment:
            deployments = Deployment.query()
            params = {'error': "true", 'flash_message': "Error - already exists!",'deployments': deployments}
            return self.render_smart_template('DEPLOYMENT','SUPERADMIN','super_admin.html',existing_deployment,params)
        else:
            newdeployment = Deployment()
            newdeployment.name = name
            newdeployment.slug = slug
            newdeployment.put()

            sleep(0.5)
            deployments = Deployment.query()
            params = {'success': "true", 'flash_message': "Successfully created deployment!",'deployments': deployments}
            self.render_smart_template('DEPLOYMENT','SUPERADMIN','super_admin.html',existing_deployment,params)


    def handle_update(self):
        name = self.request.get('name')
        old_slug = self.request.get('old_slug')
        new_slug = self.request.get('new_slug')

        existing_deployment = Deployment.get_by_slug(old_slug)

        if not existing_deployment:
            params = {'error': "true",
                      'flash_message': "Error - doesn't exist!"}
            self.render_smart_template('DEPLOYMENT','SUPERADMIN','super_admin.html',existing_deployment, params)
            return

        tmp_deployment = None

        if not (new_slug == old_slug):
            tmp_deployment = Deployment.get_by_slug(new_slug)

        if (tmp_deployment):
            deployments = MapUserToDeploymentService.get_deployments(self.user)
            params = {'error': "true", 'flash_message': "Error - already exists!",
                      'deployments': deployments}
            self.render_smart_template('DEPLOYMENT','SUPERADMIN','super_admin.html',None,params)
        else:
            existing_deployment.name = name
            existing_deployment.slug = new_slug
            existing_deployment.put()

            sleep(0.5)
            params = {}
            params['success'] = "true"
            params['flash_message'] = "Successfully updated Deployment:  " +existing_deployment.name
            self.render_smart_template('DEPLOYMENT','SUPERADMIN','super_admin.html',None,params)

    @super_admin_required
    def get(self):
        params = {}
        self.render_smart_template('DEPLOYMENT','SUPERADMIN','super_admin.html',None,{})

    @super_admin_required
    def post(self):
        method = self.request.get('method')
        if method == 'UPDATE':
            self.handle_update()
        elif method == 'CREATE':
            self.create_new_deployment()
        elif method == 'DELETE':
            self.delete_booth()
