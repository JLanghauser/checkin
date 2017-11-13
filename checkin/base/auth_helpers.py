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
from services.user_service import *
from services.deployment_service import *
from services.map_user_to_deployment_service import *
import json

def deployment_admin_required(handler):
    """
      Decorator that checks if there's a user associated with the current session.
      And that that user is an admin. Will also fail if there's no session present.
    """

    def check_deployment_admin(self, *args, **kwargs):
        auth = self.auth
        if not auth.get_user_by_session():
            if 'X-Custom-Referrer' in self.request.headers:
                self.redirect("sign_in" + '?redirect_to=' + self.request.headers['X-Custom-Referrer'], abort=True)
            else:
                self.redirect("sign_in" + '?redirect_to=' + self.request.url, abort=True)
        else:
            if (self.user.is_super_admin):
                return handler(self, *args, **kwargs)
            elif (self.user.is_deployment_admin):
                if 'deployment_key' in kwargs:
                    keyobj = ndb.Key(urlsafe=kwargs['deployment_key'])
                    mapped_users = MapUserToDeployment.query(MapUserToDeployment.deployment_key == keyobj,
                                                              MapUserToDeployment.user_key == self.user.key).fetch()
                    if count(mapped_users) > 0:
                        return handler(self, *args, **kwargs)
                    else:
                        self.redirect(self.uri_for('error'), abort=True)
                else:
                    return handler(self, *args, **kwargs)
            else:
                self.redirect(self.uri_for('error'), abort=True)
    return check_deployment_admin


def super_admin_required(handler):
    """
      Decorator that checks if there's a user associated with the current session.
      And that that user is an admin. Will also fail if there's no session present.
    """

    def check_super_admin(self, *args, **kwargs):
        auth = self.auth
        if not auth.get_user_by_session():
            if 'X-Custom-Referrer' in self.request.headers:
                self.redirect("sign_in" + '?redirect_to=' + self.request.headers['X-Custom-Referrer'], abort=True)
            else:
                self.redirect("sign_in" + '?redirect_to=' + self.request.url, abort=True)
        else:
            if self.user.is_super_admin and self.user.is_super_admin == True:
                return handler(self, *args, **kwargs)
            else:
                self.redirect(self.uri_for('error'), abort=True)
    return check_super_admin

def user_login_required(handler):
    """
      Decorator that checks if there's a user associated with the current session.
      Will also fail if there's no session present.
    """

    def check_user_login(self, *args, **kwargs):
        auth = self.auth
        if not auth.get_user_by_session():
            if 'X-Custom-Referrer' in self.request.headers:
                self.redirect("sign_in" + '?redirect_to=' + self.request.headers['X-Custom-Referrer'], abort=True)
            else:
                self.redirect("sign_in" + '?redirect_to=' + self.request.url, abort=True)
        else:
            return handler(self, *args, **kwargs)
    return check_user_login
