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
from deployment import *

class User(webapp2_extras.appengine.auth.models.User):
    is_super_admin = ndb.BooleanProperty()
    is_deployment_admin = ndb.BooleanProperty()
    username = ndb.StringProperty()
    profile = ndb.TextProperty()
    vendorname = ndb.StringProperty()
    email = ndb.StringProperty()
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
        elif self.is_deployment_admin and self.is_deployment_admin == True:
            qry = MapUserToDeployment.query(MapUserToDeployment.user_key == self.key)
            map_deps_keys = qry.fetch(projection=[MapUserToDeployment.deployment_key])
            deployments = ndb.get_multi(map_deps_keys)
            return deployments
        else:
            return []

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
