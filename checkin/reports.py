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
from random import randint
import unicodedata
from time import sleep
import csv
import StringIO
import json


class ReportsHandler(BaseHandler):
    def get_booth_report(self,deployment=None):
        report = []
        if deployment:
            map_list = MapUserToDeployment.query(MapUserToDeployment.deployment_key == deployment.key)
            for map_item in map_list:
                user = User.query(User.key == map_item.user_key).fetch(1)
                if user and len(user) > 0 and user[0] and not user[0].is_super_admin:
                    report_row = {}
                    report_row['username'] = user[0].username
                    report_row['email'] = user[0].username
                    if ("<h1>Edit your profile" in user[0].profile
                        and ">here</a></h1>" in user[0].profile
                        and len(user[0].profile) < 60):
                        report_row['hasedited'] = 'NO'
                    else:
                        report_row['hasedited'] = 'YES'
                    report.append(report_row)
        return report

    def get_deployment_params(self,deployment,**kwargs):
        params = {}
        params['logo_url'] = deployment.logo_url
        params['header_color'] = deployment.header_background_color
        params['footer_text'] =  deployment.footer_text
        for key, value in kwargs.items():
            params[key] = value
        return params

    @deployment_admin_required
    def get(self, deployment_slug=None):
        selected_deployment_slug = self.request.get('selected_deployment_slug', None)
        deployments = Deployment.query().fetch()
        if selected_deployment_slug:
            deployment_slug = selected_deployment_slug
        params = {}
        params['deployments'] = deployments
        if deployment_slug:
            dep = Deployment.get_by_slug(deployment_slug)
            if dep:
                params['boothreport'] = self.get_booth_report(dep)

        self.render_template('reports.html',params)

    @deployment_admin_required
    def post(self, deployment_slug=None):
        selected_deployment_slug = self.request.get('selected_deployment_slug', None)
        deployments = Deployment.query().fetch()
        if selected_deployment_slug:
            deployment_slug = selected_deployment_slug
        params = {}
        params['deployments'] = deployments
        if deployment_slug:
            dep = Deployment.get_by_slug(deployment_slug)
            if dep:
                params['boothreport'] = self.get_booth_report(dep)

        self.render_template('reports.html',params)
