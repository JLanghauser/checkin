#!/usr/bin/env python
import time
import webapp2_extras.appengine.auth.models
from google.appengine.ext import ndb
from webapp2_extras import security
from poster.encode import multipart_encode, MultipartParam
from poster.streaminghttp import register_openers
from google.appengine.api import images
from google.appengine.ext import db, ndb, blobstore
from google.appengine.api import urlfetch
from time import sleep
import cgi
import datetime
import webapp2
from array import *
from base.basehandler import *
from google.appengine.ext import ndb
from google.appengine.api import users
from google.appengine.ext.webapp import blobstore_handlers
from random import randint
import unicodedata
from time import sleep
import csv
import StringIO
import json
from visitor import *
from map_user_to_deployment import *
from map_user_to_visitor import *

class Deployment(ndb.Model):
    name = ndb.TextProperty(indexed=True)
    slug = ndb.TextProperty(indexed=True)
    custom_dns = ndb.TextProperty(indexed=True)
    custom_subdomain = ndb.TextProperty(indexed=True)
    logo = ndb.BlobKeyProperty()
    logo_url = ndb.ComputedProperty(lambda self: self.get_logo_url())
    header_background_color = ndb.TextProperty(indexed=True)
    footer_text = ndb.TextProperty(indexed=True)
    sample_qr_code = ndb.BlobKeyProperty()
    sample_qr_code_url = ndb.ComputedProperty(lambda self: self.get_sample_qr_code_url())
    student_link = ndb.TextProperty(indexed=True)
    student_link_text = ndb.TextProperty(indexed=True)
    user_link = ndb.TextProperty(indexed=True)
    user_link_text = ndb.TextProperty(indexed=True)
    max_visitor_id = ndb.IntegerProperty(indexed=True)

    def get_logo_url(self):
        if self.logo:
            return images.get_serving_url(self.logo, 1600, False, True)
        else:
            return ""

    def get_sample_qr_code_url(self):
        if self.sample_qr_code:
            return images.get_serving_url(self.sample_qr_code, 1600, False, True)
        else:
            return ""

    @classmethod
    def get_by_slug(cls, slug, subject='auth'):
        """Returns a deployment object based on a slug.

            :param slug:
                The slug of the requested deployment.

            :returns:
                returns user or none if
        """
        qry = Deployment.query(Deployment.slug == slug)
        deployment = qry.get()

        if deployment:
            return deployment
        return None

    def get_visitors(self):
        visitors = Visitor.query(Visitor.deployment_key == self.key)
        return visitors

    def get_users(self):
        qry2 = MapUserToDeployment.query(MapUserToDeployment.deployment_key == self.key)
        map_users_keys = qry2.fetch(projection=[MapUserToDeployment.user_key])
        users = []
        for mp in map_users_keys:
            u = mp.user_key.get()
            users.append(u)
        #users = ndb.get_multi(map_users_keys)
        return users

    def get_random_visitor(self):
        entity_count = MapUserToVisitor.query(MapUserToVisitor.deployment_key == self.key).count()
        if (entity_count > 0):
            random_index = randint(0, entity_count - 1)
            maps = MapUserToVisitor.query(MapUserToVisitor.deployment_key == self.key).order(MapUserToVisitor.key).fetch()

            counter = 0
            for map_item in maps:
                if (random_index == counter):
                    key = map_item.visitor_key
                    rand_visitor = Visitor.get_by_id(
                        key.id(), parent=key.parent(), app=key.app(), namespace=key.namespace())
                    return rand_visitor.visitor_id
                counter = counter + 1
        return None

    def upload_qr_code(self,qrcodeimg,image_type):
        multipart_param = MultipartParam(
            'file', qrcodeimg, filename='sample_'+ self.slug, filetype=image_type)
        datagen, headers = multipart_encode([multipart_param])
        upload_url = blobstore.create_upload_url('/upload_image')

        result = urlfetch.fetch(
            url=upload_url,
            payload="".join(datagen),
            method=urlfetch.POST,
            headers=headers)

        blob = blobstore.get(json.loads(result.content)["key"])
        self.sample_qr_code = blob.key()
        self.put()

    def upload_image_data(self,image_file):
        filetype = 'image/jpg'
        filename = 'test'

        multipart_param = MultipartParam(
            'file', image_file, filename=filename, filetype=filetype)
        datagen, headers = multipart_encode([multipart_param])
        upload_url = blobstore.create_upload_url('/upload_image')
        result = urlfetch.fetch(
            url=upload_url,
            payload="".join(datagen),
            method=urlfetch.POST,
            headers=headers)

        blob = blobstore.get(json.loads(result.content)["key"])

        self.logo = blob.key()
        self.put()

    def generate_visitors(self,num_to_generate):
        return

    def add_user(self, username, vendorname, password, is_deployment_admin, email):
        tmp_user = User.get_by_username(username)

        if tmp_user:
            return "Error - user " + username + " already exists."
        else:
            if not username:
                return "Error - username cannot be blank."

            newuser = User()
            newuser.username = username
            newuser.vendorname = vendorname
            newuser.set_password(password)
            newuser.is_deployment_admin = is_deployment_admin in ['true', 'True', '1', 'on']
            newuser.profile = '<h1>Edit your profile <a href = "edit">here</a></h1>'
            newuser.email = email
            newuser.put()
            sleep(0.5)

            new_map = MapUserToDeployment()
            new_map.user_key = newuser.key
            new_map.deployment_key = self.key
            new_map.put()
            sleep(0.5)
            return ""

    def edit_user(self, old_username, new_username, vendorname, password, is_deployment_admin, email):
        edit_user = User.get_by_username(old_username)

        if edit_user:
            if not (new_username.lower() == old_username.lower()):
                tmp_user = User.get_by_username(new_username)

                if tmp_user:
                    return "Error - user " + new_username + " already exists."

                edit_user.username = new_username

            edit_user.vendorname = vendorname

            if (password != edit_user.password):
                edit_user.set_password(password)

            edit_user.is_deployment_admin = is_deployment_admin in [
                'true', 'True', '1', 'on']
            edit_user.email = email
            edit_user.put()

            maps = MapUserToDeployment.query(MapUserToDeployment.user_key == edit_user.key)
            for map in maps:
                map.key.delete()

            new_map = MapUserToDeployment()
            new_map.user_key = edit_user.key
            new_map.deployment_key = self.key
            new_map.put()
            sleep(0.5)
            return ""
        return "Could not find user"

    def delete_user(self,username):
        delete_user = User.get_by_username(username)

        maps = MapUserToDeployment.query(MapUserToDeployment.user_key == delete_user.key)
        for map in maps:
            map.key.delete()

        delete_user.key.delete()
        sleep(0.5)
        return ""

    def upload_img(self, logo_url):
        image_url = logo_url
        filetype = 'image/%s' % image_url.split('.')[-1]
        if len(filetype) > 10:
            filetype = 'image/jpg'

        filename = image_url.split('/')[-1]
        raw_img = None

        result = urlfetch.fetch(image_url)
        if result.status_code == 200:
            raw_img = result.content
        else:
            return "error fetching URL"

        multipart_param = MultipartParam(
            'file', raw_img, filename=filename, filetype=filetype)
        datagen, headers = multipart_encode([multipart_param])
        upload_url = blobstore.create_upload_url('/upload_image')
        result = urlfetch.fetch(
            url=upload_url,
            payload="".join(datagen),
            method=urlfetch.POST,
            headers=headers)

        blob = blobstore.get(json.loads(result.content)["key"])

        self.logo = blob.key()
        self.put()
