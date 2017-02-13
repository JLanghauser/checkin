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

class CheckInHandler(BaseHandler):
    def handlerequest(self, deployment_slug=None):
        visitor_id = self.request.get('visitor_id', -1)
        deployment = None
        params = {}
        post_deployment_slug = self.request.get('deployment_slug', None)

        if deployment_slug:
            deployment = Deployment.get_by_slug(deployment_slug)

        if not deployment and post_deployment_slug:
            deployment = Deployment.get_by_slug(post_deployment_slug)

        if deployment:
            params = self.add_deployment_params({},deployment)

        if (visitor_id == -1):
            self.render_template('checkin_visitor.html',params)
        else:

            if not deployment:
                params['error'] = "true"
                params['flash_message'] = "Invalid or No Deployment Passed"
                self.render_template('checkin_visitor.html', params)
                return

            new_map = MapUserToVisitor()
            new_map.user_key = self.user.key
            qry = Visitor.query(Visitor.visitor_id == visitor_id,
                                Visitor.deployment_key == deployment.key)
            visitor = qry.get()
            if (visitor or visitor_id == 9999999):
                maps = MapUserToVisitor.query(ndb.AND(
                    MapUserToVisitor.visitor_key == visitor.key,
                    MapUserToVisitor.user_key == self.user.key,
                    MapUserToVisitor.deployment_key == deployment.key)
                ).count(1)

                if (maps == 0):
                    new_map.visitor_key = visitor.key
                    new_map.deployment_key = visitor.deployment_key
                    new_map.date_created = datetime.utcnow()
                    new_map.put()
                    params['visitor_id'] = visitor_id
                    self.render_template('successful_checkin.html', params)
                else:
                    params['error'] = 'true'
                    params['flash_message'] = "You've already checked in visitor " + visitor_id
                    self.render_template('checkin_visitor.html', params)
            else:
                params['error'] = 'true'
                params['flash_message'] = 'Cannot find visitor ' + visitor_id
                self.render_template('checkin_visitor.html', params)

    @user_login_required
    def get(self, deployment_slug=None):
        self.handlerequest(deployment_slug)

    @user_login_required
    def post(self, deployment_slug=None):
        self.handlerequest(deployment_slug)

class RandomVisitorHandler(BaseHandler):
    @deployment_admin_required
    def get(self,deployment_slug):
        dep = Deployment.get_by_slug(deployment_slug)
        if dep:
            params = self.add_deployment_params({},dep)

            # get count
            entity_count = MapUserToVisitor.query(MapUserToVisitor.deployment_key == dep.key).count()

            # get random number
            random_index = randint(0, entity_count - 1)

            # Get all the keys, not the Entities
            maps = MapUserToVisitor.query(MapUserToVisitor.deployment_key == dep.key).order(MapUserToVisitor.key).fetch()

            counter = 0
            for map_item in maps:
                if (random_index == counter):
                    key = map_item.visitor_key
                    rand_visitor = Visitor.get_by_id(
                        key.id(), parent=key.parent(), app=key.app(), namespace=key.namespace())
                    params['visitor_id'] = rand_visitor.visitor_id
                    self.render_template('raffle_results.html', params)
                    return
                counter = counter + 1
