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
import qrcode
import qrcode.image.svg
from qrcode.image.pure import PymagingImage
from base.qrcodegen import *
from models.deployment import *

class AdminHandler(BaseHandler):
    def delete_booth(self,deployment_slug):
        existing_deployment = Deployment.get_by_slug(deployment_slug)
        params = {}
        params['activetab'] = 'booths'
        username = self.request.get('edit-username')
        retval = existing_deployment.delete_user(username)

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
        email = self.request.get('edit-email')
        admin = self.request.get('edit-admin')
        retval = existing_deployment.edit_user(old_username, username, vendorname, password, admin, email)

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
        email = self.request.get('email')
        admin = self.request.get('admin')
        retval = existing_deployment.add_user(username,vendorname,password,admin,email)

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
        qr_codes_to_generate = self.request.get('qr_codes_to_generate')
        #existing_deployment.generate_visitors(qr_codes_to_generate)

    def random_visitor(self,deployment_slug):
        existing_deployment = Deployment.get_by_slug(deployment_slug)
        params = {}
        params['random_visitor'] =  existing_deployment.get_random_visitor()
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

        if not (new_slug == deployment_slug):
            tmp_deployment_slug = Deployment.query(
                Deployment.slug == new_slug).fetch(1)

        if not (custom_dns == existing_deployment.custom_dns):
            tmp_deployment_custom_dns = Deployment.query(Deployment.custom_dns == custom_dns,
                                                         Deployment.custom_subdomain == custom_subdomain).fetch(1)

        if ((tmp_deployment_slug and len(tmp_deployment_slug)) or
                (tmp_deployment_custom_dns and len(tmp_deployment_custom_dns))):
            deployments = self.user.get_deployments()
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

            sleep(0.5)
            deployments = self.user.get_deployments()
            params['success'] = "true"
            params['flash_message'] = "Successfully update Deployment:  " +existing_deployment.name
            self.render_smart_template('DEPLOYMENT',referring_page,'deployments_index.html',existing_deployment,params)

    @deployment_admin_required
    def get(self,deployment_slug):
        dep = Deployment.get_by_slug(deployment_slug)
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
            self.upload_qr_codes(self.request,deployment_slug)
        elif method == 'EXPORT_QR_CODES':
            self.export_qr_codes(self.request,deployment_slug)
        elif method == 'CREATE_NEW_BOOTH':
            self.create_new_booth(deployment_slug)
        elif method == 'UPLOAD_BOOTHS':
            self.upload_booths(self.request,deployment_slug)
        elif method == 'EDIT_BOOTH':
            self.edit_booth(deployment_slug)
        elif method == 'DELETE_BOOTH':
            self.delete_booth(deployment_slug)
        elif method == 'RANDOM_VISITOR':
            self.random_visitor(deployment_slug)
        elif method == 'DOWNLOAD_RAW_CHECKINS':
            self.download_raw_checkins(self.request,deployment_slug)
