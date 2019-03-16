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
from services.map_user_to_visitor_service import *
from services.map_user_to_deployment_service import *
from google.appengine.ext import deferred
from services.child_process_service import *
from services.generator_service import *

class AdminHandler(BaseHandler):
    def upload_qr_codes(self,deployment_slug):
        existing_deployment = Deployment.get_by_slug(deployment_slug)
        params = {}
        params['activetab'] = 'qrcodes'
        bulkfile = self.request.get('bulkfile')
        retval = DeploymentService.add_bulk_visitors(existing_deployment, bulkfile)

        if retval is not "":
            params['error'] = "true"
            params['flash_message'] = retval
        else:
            params['success'] = "true"
            params['flash_message'] = "Successfully Created QRCodes"

        self.render_smart_template('DEPLOYMENT','ADMIN','deployments_index.html',existing_deployment,params)

    def upload_booths(self,deployment_slug):
        existing_deployment = Deployment.get_by_slug(deployment_slug)
        params = {}
        params['activetab'] = 'booths'
        bulkfile = self.request.get('bulkfile')
        retval = MapUserToDeploymentService.add_users_in_bulk(existing_deployment, bulkfile)

        if retval is not "":
            params['error'] = "true"
            params['flash_message'] = retval
        else:
            params['success'] = "true"
            params['flash_message'] = "Successfully Created Booths"

        self.render_smart_template('DEPLOYMENT','ADMIN','deployments_index.html',existing_deployment,params)

    def delete_booth(self,deployment_slug):
        existing_deployment = Deployment.get_by_slug(deployment_slug)
        params = {}
        params['activetab'] = 'booths'
        username = self.request.get('edit-username')
        retval = MapUserToDeploymentService.delete_user(existing_deployment,username)

        if retval is not "":
            params['error'] = "true"
            params['flash_message'] = retval
        else:
            params['success'] = "true"
            params['flash_message'] = "Successfully Deleted User:  " + username

        self.render_smart_template('DEPLOYMENT','ADMIN','deployments_index.html',existing_deployment,params)

    def edit_booth(self,deployment_slug):
        existing_deployment = Deployment.get_by_slug(deployment_slug)
        params = {}
        params['activetab'] = 'booths'
        old_username = self.request.get('old-username')
        username = self.request.get('edit-username')
        vendorname = self.request.get('edit-vendorname')
        password = self.request.get('edit-password')
        category = self.request.get('edit-category')
        admin = self.request.get('edit-admin')
        retval = MapUserToDeploymentService.edit_user(existing_deployment, old_username, username, vendorname, password, admin, category)

        if retval is not "":
            params['error'] = "true"
            params['flash_message'] = retval
        else:
            params['success'] = "true"
            params['flash_message'] = "Successfully Edited User:  " + username

        self.render_smart_template('DEPLOYMENT','ADMIN','deployments_index.html',existing_deployment,params)

    def create_new_booth(self,deployment_slug):
        existing_deployment = Deployment.get_by_slug(deployment_slug)
        params = {}
        params['activetab'] = 'booths'
        username = self.request.get('username')
        vendorname = self.request.get('vendorname')
        password = self.request.get('password')
        admin = self.request.get('admin')
        retval = MapUserToDeploymentService.add_user(existing_deployment,username,vendorname,password,admin)

        if retval is not "":
            params['error'] = "true"
            params['flash_message'] = retval
        else:
            params['success'] = "true"
            params['flash_message'] = "Successfully created User:  " + username

        self.render_smart_template('DEPLOYMENT','ADMIN','deployments_index.html',existing_deployment,params)

    def generate_qr_codes(self,deployment_slug):
        existing_deployment = Deployment.get_by_slug(deployment_slug)
        params = {}
        params['activetab'] = 'qrcodes'
        start_at_one = self.request.get('start_at_one')
        qr_codes_to_generate = self.request.get('qr_codes_to_generate')
        VisitorService.generate_visitors(existing_deployment, int(qr_codes_to_generate),self.user,start_at_one)
        existing_deployment.qr_codes_zip = None
        existing_deployment.put()
        params['success'] = "true"
        params['flash_message'] = "Successfully started generating QRcodes"
        self.render_smart_template('DEPLOYMENT','ADMIN','deployments_index.html',existing_deployment,params)

    def random_visitor(self,deployment_slug):
        existing_deployment = Deployment.get_by_slug(deployment_slug)
        params = {}
        params['random_visitor'] =  MapUserToVisitorService.get_random_visitor(existing_deployment)
        params['activetab'] = 'raffle'
        self.render_smart_template('DEPLOYMENT','ADMIN','deployments_index.html',existing_deployment,params)

    def handle_update(self,deployment_slug):
        name = self.request.get('name')
        new_slug = self.request.get('slug')
        custom_dns = self.request.get('custom_dns')
        custom_subdomain = self.request.get('custom_subdomain')
        logo_url = self.request.get('logo_url')
        header_background_color = self.request.get('header_background_color')
        footer_text = self.request.get('footer_text')
        student_link = self.request.get('student_link')
        student_link_text = self.request.get('student_link_text')
        user_link = self.request.get('user_link')
        user_link_text = self.request.get('user_link_text')
        referring_page = self.request.get('referring_page')
        image_file = self.request.get('image_file')

        existing_deployment = Deployment.get_by_slug(deployment_slug)

        if len(header_background_color) > 0 and header_background_color[0] == '#':
            header_background_color = header_background_color[1:]

        if len(header_background_color) > 6:
            params = {'error': "true",
                      'flash_message': "Error - background color should be an html color code (6 characters long)"}
            self.render_smart_template('DEPLOYMENT',referring_page,'deployments_index.html',existing_deployment, params)
            return

        if not existing_deployment:
            params = {'error': "true",
                      'flash_message': "Error - doesn't exist!"}
            self.render_smart_template('DEPLOYMENT',referring_page,'deployments_index.html',existing_deployment, params)
            return

        tmp_deployment_slug = None
        tmp_deployment_custom_dns = None
        tmp_deployment_subdomain = None
        update_all_qr_codes = False

        if not (new_slug == deployment_slug):
            tmp_deployment_slug = Deployment.query(
                Deployment.slug == new_slug).fetch(1)

        if not (custom_dns == existing_deployment.custom_dns):
            tmp_deployment_custom_dns = Deployment.query(Deployment.custom_dns == custom_dns,
                                                         Deployment.custom_subdomain == custom_subdomain).fetch(1)
            update_all_qr_codes = True

        if not (custom_subdomain == existing_deployment.custom_subdomain):
            update_all_qr_codes = True

        if ((tmp_deployment_slug and len(tmp_deployment_slug)) or
                (tmp_deployment_custom_dns and len(tmp_deployment_custom_dns))):
            deployments = MapUserToDeploymentService.get_deployments(self.user)
            params = {'error': "true", 'flash_message': "Error - already exists!",
                      'deployments': deployments}
            self.render_smart_template('DEPLOYMENT',referring_page,'deployments_index.html',existing_deployment,params)
        else:
            params = {}
            if (existing_deployment.custom_dns != custom_dns or
                existing_deployment.custom_subdomain != custom_subdomain):
               params['activetab'] = 'domain'
            elif (existing_deployment.name != name or
                existing_deployment.header_background_color != header_background_color or
                existing_deployment.logo_url != logo_url or
                existing_deployment.footer_text != footer_text):
               params['activetab'] = 'look'
            elif (existing_deployment.student_link != student_link or
                existing_deployment.student_link_text != student_link_text or
                existing_deployment.user_link != user_link or
                existing_deployment.user_link_text != user_link_text):
               params['activetab'] = 'surveys'

            existing_deployment.name = name
            existing_deployment.slug = new_slug
            existing_deployment.custom_dns = custom_dns
            existing_deployment.custom_subdomain = custom_subdomain
            existing_deployment.header_background_color = header_background_color
            existing_deployment.footer_text = footer_text
            existing_deployment.student_link = student_link
            existing_deployment.student_link_text = student_link_text
            existing_deployment.user_link = user_link
            existing_deployment.user_link_text = user_link_text
            existing_deployment.put()

            if existing_deployment.logo_url != logo_url:
                existing_deployment.upload_img(logo_url)

            if image_file and image_file != "":
                existing_deployment.upload_image_data(image_file)
                params['activetab'] = 'look'

            DeploymentService.set_sample_qr_code(existing_deployment)
            existing_deployment.put()
            if update_all_qr_codes == True:
                existing_deployment.qr_codes_zip = None
                existing_deployment.put()
                GeneratorService.update_all_qr_codes(existing_deployment, self.user)

            sleep(0.5)
            params['success'] = "true"
            params['flash_message'] = "Successfully updated Deployment:  " +existing_deployment.name
            self.render_smart_template('DEPLOYMENT',referring_page,'deployments_index.html',existing_deployment,params)

    @deployment_admin_required
    def get(self,deployment_slug):
        dep = Deployment.get_by_slug(deployment_slug)
        method = self.request.get('method')
        if method and method == 'GENERATE_QR_CODES':
            self.generate_qr_codes(deployment_slug)

        params = self.add_deployment_params({},dep)
        self.render_smart_template('DEPLOYMENT','ADMIN','admin.html',dep,params)




    @deployment_admin_required
    def post(self, deployment_slug):
        method = self.request.get('method')
        if method == 'UPDATE':
            self.handle_update(deployment_slug)
        elif method == 'GENERATE_QR_CODES':
            self.generate_qr_codes(deployment_slug)
        elif method == 'UPLOAD_QR_CODES':
            self.upload_qr_codes(deployment_slug)
        elif method == 'EXPORT_QR_CODES':
            self.export_qr_codes(self.request,deployment_slug)
        elif method == 'CREATE_NEW_BOOTH':
            self.create_new_booth(deployment_slug)
        elif method == 'UPLOAD_BOOTHS':
            self.upload_booths(deployment_slug)
        elif method == 'EDIT_BOOTH':
            self.edit_booth(deployment_slug)
        elif method == 'DELETE_BOOTH':
            self.delete_booth(deployment_slug)
        elif method == 'RANDOM_VISITOR':
            self.random_visitor(deployment_slug)
