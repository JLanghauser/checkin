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
from basehandler import *
from google.appengine.ext import ndb
from google.appengine.api import users
from google.appengine.ext.webapp import blobstore_handlers
from random import randint
import unicodedata
from time import sleep
import csv
import StringIO
import json

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

class User(webapp2_extras.appengine.auth.models.User):
    is_super_admin = ndb.BooleanProperty()
    is_deployment_admin = ndb.BooleanProperty()
    username = ndb.StringProperty()
    profile = ndb.TextProperty()
    vendorname = ndb.StringProperty()
    username_lower = ndb.ComputedProperty(lambda self: self.username.lower())

class MapUserToDeployment (ndb.Model):
    deployment_key = ndb.KeyProperty(kind=Deployment)
    user_key = ndb.KeyProperty(kind=User)

class User(webapp2_extras.appengine.auth.models.User):
    is_super_admin = ndb.BooleanProperty()
    is_deployment_admin = ndb.BooleanProperty()
    username = ndb.StringProperty()
    profile = ndb.TextProperty()
    vendorname = ndb.StringProperty()
    username_lower = ndb.ComputedProperty(lambda self: self.username.lower())
    def set_password(self, raw_password):
        """Sets the password for the current user

        :param raw_password:
            The raw password which will be hashed and stored
        """
        self.password = security.generate_password_hash(
            raw_password, length=12)

    def get_users(self,deployment=None):
        if self.is_super_admin and self.is_super_admin == True:
            if deployment:
                qry2 = MapUserToDeployment.query(MapUserToDeployment.deployment_key == deployment.key)
                map_users_keys = qry2.fetch(projection=[MapUserToDeployment.user_key])
                users = ndb.get_multi(map_users_keys).order(User.vendorname)
                return users
            else:
                return User.query().order(User.vendorname)
        elif self.is_deployment_admin and self.is_deployment_admin == True:
            qry = MapUserToDeployment.query(MapUserToDeployment.user_key == self.key)
            map_deps = qry.fetch(projection=[MapUserToDeployment.deployment_key])
            if deployment:
                if deployment.key in map_deps:
                    map_deps = [deployment.key]
                else:
                    return []
            qry2 = MapUserToDeployment.query(MapUserToDeployment.deployment_key.IN(map_deps))
            map_users_keys = qry2.fetch(projection=[MapUserToDeployment.user_key])
            users = ndb.get_multi(map_users_keys).order(User.vendorname)
            return users
        else:
            return []

    def get_deployments(self):
        if self.is_super_admin and self.is_super_admin == True:
            return Deployment.query().fetch()
        else:
            qry = MapUserToDeployment.query(MapUserToDeployment.user_key == self.key)
            map_deps_keys = qry.fetch(projection=[MapUserToDeployment.deployment_key])
            deployments = ndb.get_multi(map_deps_keys)
            return deployments

    @classmethod
    def get_by_auth_token(cls, user_id, token, subject='auth'):
        """Returns a user object based on a user ID and token.

        :param user_id:
            The user_id of the requesting user.
        :param token:
            The token string to be verified.
        :returns:
            A tuple ``(User, timestamp)``, with a user object and
            the token timestamp, or ``(None, None)`` if both were not found.
        """
        token_key = cls.token_model.get_key(user_id, subject, token)
        user_key = ndb.Key(cls, user_id)
        # Use get_multi() to save a RPC call.
        valid_token, user = ndb.get_multi([token_key, user_key])
        if valid_token and user:
            timestamp = int(time.mktime(valid_token.created.timetuple()))
            return user, timestamp

        return None, None

    @classmethod
    def get_by_username(cls, username, subject='auth'):
        """Returns a user object based on a username.

        :param username:
            The username of the requesting user.

        :returns:
            returns user or none if
        """
        username = username.lower()

        qry = User.query(User.username == username)
        user = qry.get()

        if user:
            return user

        qry = User.query(User.username_lower == username)
        user = qry.get()

        if user:
            return user

        return None

class Visitor(ndb.Model):
    deployment_key = ndb.KeyProperty(kind=Deployment)
    visitor_id = ndb.TextProperty(indexed=True)

class MapUserToVisitor (ndb.Model):
    deployment_key = ndb.KeyProperty(kind=Deployment)
    user_key = ndb.KeyProperty(kind=User)
    visitor_key = ndb.KeyProperty(kind=Visitor)
    date_created = ndb.DateTimeProperty()

class SudoLogin (ndb.Model):
    admin_key = ndb.KeyProperty(kind=User)
    user_key = ndb.KeyProperty(kind=User)

class BackgroundJob (ndb.Model):
    user_key = ndb.KeyProperty(kind=User)
    deployment_key = ndb.KeyProperty(kind=Deployment)
    job_type = ndb.TextProperty(indexed=True)
    status = ndb.TextProperty(indexed=True)
    status_message = ndb.TextProperty(indexed=True)
    raw_data = ndb.BlobKeyProperty()
