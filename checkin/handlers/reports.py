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


    def get_checkin_raw_data(self,deployment=None,csv_writer=None):
        report = []
        users = {}
        visitors = {}

        if deployment:
            checkins = MapUserToVisitor.query(
                            MapUserToVisitor.deployment_key == deployment.key)

            if csv_writer:
                csv_writer.writerow(['booth_user', 'booth_vendor','student_id'])

            for checkin in checkins:
                report_row = {}

                if checkin.user_key not in users:
                    user = User.query(User.key == checkin.user_key).fetch(1)
                    users[checkin.user_key] = user
                else:
                    user = users[checkin.user_key]

                if user and len(user) > 0 and user[0]:
                    user = user[0]
                else:
                    user = None

                report_row['booth_user'] = user.username if user else 'ERROR'
                report_row['booth_vendor'] = user.vendorname if user else 'ERROR'

                if checkin.visitor_key not in visitors:
                    visitor = Visitor.query(Visitor.key == checkin.visitor_key,
                                        Visitor.deployment_key == deployment.key).fetch(1)
                    visitors[checkin.visitor_key] = visitor
                else:
                    visitor = visitors[checkin.visitor_key]

                if visitor and len(visitor) > 0 and visitor[0]:
                    visitor = visitor[0]
                else:
                    visitor = None

                report_row['student_id'] = visitor.visitor_id if visitor else 'ERROR'

                report.append(report_row)
                if csv_writer:
                    csv_writer.writerow([report_row['booth_user'],report_row['booth_vendor'],report_row['student_id']])

        return report

    def get_booth_checkin_report(self,deployment=None):
        report = {}
        if deployment:
            map_list = MapUserToDeployment.query(MapUserToDeployment.deployment_key == deployment.key)
            for map_item in map_list:
                user = User.query(User.key == map_item.user_key).fetch(1)
                if user and len(user) > 0 and user[0] and not user[0].is_super_admin:
                    count = MapUserToVisitor.query(MapUserToVisitor.deployment_key == deployment.key,
                                                MapUserToVisitor.user_key == user[0].key).count()
                    report[user[0].vendorname] = count
            sorted_report_items = sorted(report.iteritems(), key=lambda r: r[1])
            sorted_report_items.reverse()
            return sorted_report_items
        return []

    def get_booth_report(self,deployment=None):
        report = []
        edited_count = 0
        unedited_count = 0
        if deployment:
            map_list = MapUserToDeployment.query(MapUserToDeployment.deployment_key == deployment.key)
            for map_item in map_list:
                user = User.query(User.key == map_item.user_key).fetch(1)
                if user and len(user) > 0 and user[0] and not user[0].is_super_admin:
                    report_row = {}
                    report_row['username'] = user[0].username
                    report_row['email'] = user[0].email
                    if ("<h1>Edit your profile" in user[0].profile
                        and ">here</a></h1>" in user[0].profile
                        and len(user[0].profile) < 60):
                        report_row['hasedited'] = 'NO'
                        unedited_count = unedited_count + 1
                    else:
                        report_row['hasedited'] = 'YES'
                        edited_count = edited_count + 1
                    report.append(report_row)
            report_stats = []
            report_stats_row = {}
            report_stats_row['unedited'] = unedited_count
            report_stats_row['edited'] = edited_count
            report_stats.append(report_stats_row)
        return report_stats,report

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
