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
from random import randint
import unicodedata
from time import sleep
import csv
import StringIO
import json
import operator
from models.deployment import *


class AsyncReportsHandler(BaseHandler):

    @deployment_admin_required
    def get(self,deployment_slug):
        deployment = Deployment.get_by_slug(deployment_slug)

        report_type = self.request.get('report_type')
        if report_type == 'RAW_CHECKINS':
            report = deployment.get_checkin_raw_data()
        elif report_type == 'BOOTH_CHECKIN_REPORT':
            report  = deployment.get_booth_checkin_report()
        elif report_type == 'BOOTH_REPORT':
            report_stats,report  = deployment.get_booth_report()

            # 'recordsTotal': total,
            # 'recordsFiltered':total,
        obj = {
            'success': 'true',
            'data': report,
            'data-stats': report_stats,
        }
        return self.render_json(obj)


class ReportsHandler(BaseHandler):
    def async_generate_report(self,user=None,deployment=None,csv_writer=None,report_type=None):
        new_stored_data = StoredData()
        report = None

        if report_type == 'RAW_CHECKINS':
            report = self.get_checkin_raw_data(deployment,csv_writer)
        elif report_type == 'BOOTH_CHECKIN_REPORT':
            report  = self.get_booth_checkin_report(deployment)
        elif report_type == 'BOOTH_REPORT':
            report  = self.get_booth_report(deployment)

        new_stored_data.user_key = user.key
        new_stored_data.deployment_key = deployment.key
        new_stored_data.data_type = report_type
        new_stored_data.raw_data = report
        new_stored_data.put()

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
                 stats, report = self.get_booth_report(dep)
                 params['boothreport_stats'] = stats
                 params['boothreport'] = report

        self.render_template('reports.html',params)

    @deployment_admin_required
    def post(self, deployment_slug=None):
        selected_deployment_slug = self.request.get('selected_deployment_slug', None)
        export = self.request.get('export', None)

        deployments = Deployment.query().fetch()
        if selected_deployment_slug:
            deployment_slug = selected_deployment_slug
        params = {}
        params['deployments'] = deployments
        if deployment_slug:
            dep = Deployment.get_by_slug(deployment_slug)
            if dep and export:
                self.response.headers['Content-Type'] = 'text/csv'
                self.response.headers['Content-Disposition'] = 'attachment; filename=deploymentexport.csv'
                writer = csv.writer(self.response.out)
                raw_data = self.get_checkin_raw_data(dep,writer)
                return
            elif dep:
                params['boothreport_stats'],params['boothreport'] = self.get_booth_report(dep)
                params['boothcheckinreport'] = self.get_booth_checkin_report(dep)

        self.render_template('reports.html',params)
