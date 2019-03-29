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
from services.user_service import *
from reports import *
from sample import *
from pages import *
from services.deployment_service import *
from models.raffle_entry import *
from models.raffle_rule import *

class StudentHandler(BaseHandler):
    def get_deployment_params(self,deployment,visitor=None):
        params = {}
        params['logo_url'] = deployment.logo_url
        params['header_color'] = deployment.header_background_color
        params['footer_text'] =  deployment.footer_text
        params['student_link'] =  deployment.student_link
        params['student_link_text'] =  deployment.student_link_text
        params['max_raffle_entries'] =  deployment.max_raffle_entries

        or_rules = RaffleRule.query(RaffleRule.deployment_key == deployment.key,
                                         RaffleRule.operator == 'OR').order(RaffleRule.key).fetch()

        and_rules = RaffleRule.query(RaffleRule.deployment_key == deployment.key,
                                 RaffleRule.operator == 'AND').order(RaffleRule.key).fetch()

        if visitor != None:
            for indx, or_rule in enumerate(or_rules):
                if visitor and visitor.or_progress and len(visitor.or_progress) > indx:
                    or_rule.progress = visitor.or_progress[indx]
                    or_rule.num_progress = int(round(visitor.or_progress[indx] * or_rule.num_checkins / 100.0))
                    or_rule.remaining = or_rule.num_checkins - or_rule.num_progress
                else:
                    or_rule.progress = 0
                    or_rule.num_progress = 0
                    or_rule.remaining = or_rule.num_checkins

            for indx, and_rule in enumerate(and_rules):
                if visitor and visitor.and_progress and len(visitor.and_progress) > indx:
                    and_rule.progress = visitor.and_progress[indx]
                    and_rule.num_progress = int(round(visitor.and_progress[indx] * and_rule.num_checkins / 100.0))
                    and_rule.remaining = and_rule.num_checkins - and_rule.num_progress
                else:
                    and_rule.progress = 0
                    and_rule.num_progress = 0
                    and_rule.remaining = and_rule.num_checkins

        params['or_rules'] = or_rules
        params['and_rules'] = and_rules
        return params

    def get_table_of_contents(self, deployment, visitor):
        toc = ""
        categories = UserService.get_groups(deployment=deployment)
        for category in categories:
            if category.category == None:
                toc += "<h5><B>Booths...</B></h5>"
            else:
                toc += "<h5><B>" + category.category + "...</B></h5>"

            maps = MapUserToVisitor.query(
                MapUserToVisitor.visitor_key == visitor.key,
                MapUserToVisitor.deployment_key == deployment.key,
                MapUserToVisitor.category == category.category).order(MapUserToVisitor.vendorname).fetch()

            if len(maps) == 0:
                if category.category == None:
                    toc += "<h6>You haven't checked into any booths yet</h6>"
                else:
                    toc += "<h6>You haven't checked into any " + category.category + " booths yet</h6>"
            else:
                for map in maps:
                    ukey = map.user_key
                    u = ukey.get()
                    toc += "<a href='#" + u.vendorname + "'><h6>" + u.vendorname + "</h6></a>"
        return toc

    def handlerequest(self, deployment_slug=None):
        visitor_id = self.request.get('visitor_id', '').strip()

        if (visitor_id == '' or not deployment_slug):
            self.render_template('error_page.html')
        else:
            deployment = Deployment.get_by_slug(deployment_slug)

            if not deployment:
                self.render_template('error_page.html')

            qry = Visitor.query(Visitor.visitor_id == visitor_id,
                                Visitor.deployment_key == deployment.key)
            visitor = qry.get()
            params = []
            if visitor:
                params = self.get_deployment_params(deployment,visitor)
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
                        profiles.append("<h2 id='" + u.vendorname + "'>" + u.vendorname + "</h2>" +
                                        "<h3>This organization hasn't included any information)</h3>")
                    else:
                        profiles.append(
                            "<h2 id='" + u.vendorname + "'>" + u.vendorname + "</h2>" + u.profile)
                params['profiles'] = profiles

                entries = RaffleEntry.query(RaffleEntry.visitor_key == visitor.key).count()
                params['raffle_entries'] = entries
                params['table_of_contents'] = self.get_table_of_contents(deployment=deployment, visitor=visitor)

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
