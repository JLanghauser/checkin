#!/usr/bin/env python
import time
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
import webapp2_extras.appengine.auth.models

class User(webapp2_extras.appengine.auth.models.User):
    is_super_admin = ndb.BooleanProperty()
    is_deployment_admin = ndb.BooleanProperty()
    username = ndb.StringProperty()
    profile = ndb.TextProperty()
    vendorname = ndb.StringProperty()
    category = ndb.StringProperty()
    category_lower = ndb.ComputedProperty(lambda self: self.category.lower() if self.category else None )
    username_lower = ndb.ComputedProperty(lambda self: self.username.lower())
    deployment_key = ndb.KeyProperty(kind=Deployment,indexed=True)

    def set_password(self, raw_password):
        """Sets the password for the current user

        :param raw_password:
            The raw password which will be hashed and stored
        """
        self.password = security.generate_password_hash(
            raw_password, length=12)


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
