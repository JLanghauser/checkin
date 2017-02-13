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
from reports import *
from sample import *
from pages import *
from models.deployment import *

class DeploymentHandler(BaseHandler):
    @deployment_admin_required
    def post(self, deployment_slug):
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

        existing_deployment = Deployment.get_by_slug(deployment_slug)

        if header_background_color[0] == '#':
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

            sleep(0.5)
            deployments = self.user.get_deployments()
            params = {'success': "true", 'flash_message': "Successfully update Deployment:  " +
                      existing_deployment.name, 'deployments': deployments}
            self.render_smart_template('DEPLOYMENT',referring_page,'deployments_index.html',existing_deployment,params)

class DeploymentsHandler(BaseHandler):

    @deployment_admin_required
    def get(self):
        editing_slug = self.request.get('editing_slug', '')
        deployments = Deployment.query()
        params = {'deployments': deployments, 'editing_slug': editing_slug}
        self.render_template('deployments_index.html', params)

    @super_admin_required
    def post(self):
        name = self.request.get('name')
        slug = self.request.get('slug')
        custom_dns = self.request.get('custom_dns')
        custom_subdomain = self.request.get('custom_subdomain')
        logo_url = self.request.get('logo_url', '')
        header_background_color = self.request.get('header_background_color')
        footer_text = self.request.get('footer_text')
        student_link = self.request.get('student_link')
        student_link_text = self.request.get('student_link_text')
        user_link = self.request.get('user_link')
        user_link_text = self.request.get('user_link_text')

        if len(header_background_color) > 6:
            params = {'error': "true",
                      'flash_message': "Error - background color should be an html color code (6 characters long)"}
            self.render_template('deployments_index.html', params)
            return

        tmp_deployment_slug = Deployment.query(
            Deployment.slug == slug).fetch(1)
        tmp_deployment_custom_dns = Deployment.query(Deployment.custom_dns == custom_dns,
                                                     Deployment.custom_subdomain == custom_subdomain).fetch(1)

        if ((tmp_deployment_slug and len(tmp_deployment_slug)) or
                (tmp_deployment_custom_dns and len(tmp_deployment_custom_dns))):
            deployments = Deployment.query()
            params = {'error': "true", 'flash_message': "Error - already exists!",
                      'deployments': deployments}
            self.render_template('deployments_index.html', params)
        else:
            newdeployment = Deployment()
            newdeployment.name = name
            newdeployment.slug = slug
            newdeployment.custom_dns = custom_dns
            newdeployment.custom_subdomain = custom_subdomain
            newdeployment.header_background_color = header_background_color
            newdeployment.footer_text = footer_text
            newdeployment.student_link = student_link
            newdeployment.student_link_text = student_link_text
            newdeployment.user_link = user_link
            newdeployment.user_link_text = user_link_text

            newdeployment.put()
            if logo_url:
                newdeployment.upload_img(logo_url)
            sleep(0.5)
            deployments = Deployment.query()
            params = {'success': "true", 'flash_message': "Successfully created Deployment:  " +
                      newdeployment.name, 'deployments': deployments}
            self.render_template('deployments_index.html', params)
