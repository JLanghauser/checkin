from google.appengine.ext import ndb
from google.appengine.api import users
from deployment import *
from user import *

class Deployment(ndb.Model):
    name = ndb.TextProperty(indexed=True)

class BackgroundJob (ndb.Model):
    user_key = ndb.KeyProperty(kind=User)
    deployment_key = ndb.KeyProperty(kind=Deployment)
    job_type = ndb.IntegerProperty(indexed=True)
    status_message = ndb.TextProperty(indexed=True)
    status = ndb.IntegerProperty(indexed=True)

    @classmethod
    def create_new(cls, user_key, deployment_key, job_type):
        newjob = BackgroundJob()
        newjob.user_key = user_key
        newjob.deployment_key = deployment_key
        newjob.job_type = job_type
        newjob.status = 0
        newjob.put()
        return newjob

class ChildProcess (ndb.Model):
    background_job_key = ndb.KeyProperty(kind=BackgroundJob)

    @classmethod
    def create_new(cls, background_job_key):
        newprocess = ChildProcess()
        newprocess.background_job_key = background_job_key
        newprocess.put()
        return newprocess
