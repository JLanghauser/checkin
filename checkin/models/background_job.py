from google.appengine.ext import ndb
from google.appengine.api import users
from deployment import *
from user import *

class BackgroundJob (ndb.Model):
    user_key = ndb.KeyProperty(kind=User)
    deployment_key = ndb.KeyProperty(kind=Deployment)
    job_type = ndb.IntegerProperty(indexed=True)
    status_message = ndb.TextProperty(indexed=True)
    status = ndb.IntegerProperty(indexed=True)

class ChildProcess (ndb.Model):
    background_job_key = ndb.KeyProperty(kind=BackgroundJob)
