#!/usr/bin/env python
from globalconstants import *
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
from reports import *
from sample import *
from pages import *
from base.basehandler import *
from models.background_job import *
from models.deployment import *

class BackgroundJobs(BaseHandler):
    @deployment_admin_required
    def get(self,deployment_slug):
        user = self.user
        dep = Deployment.get_by_slug(deployment_slug)
        jobs = BackgroundJob.query(BackgroundJob.deployment_key == dep.key,
                                   BackgroundJob.status.IN([1,2]))
        for job in jobs:
            children = ChildProcess.query(
                                ChildProcess.background_job_key == job.key).count()

            progress = 100.0 - int(100/NUM_BACKGROUND_JOB_WORKERS * children)

            if job.status == 2:
                job.key.delete()
            elif children == 0:
                job.status = 2
                job.status_message = 'Finished job.'
                job.put()
            elif job.job_type == 0:
                job.status_message = 'Adding Badges to system: ' + str(progress) + ' percent complete'
                job.put()
            elif job.job_type == 1:
                job.status_message = 'Updating all badges: ' + str(progress) + ' percent complete'
                job.put()

        jobs = BackgroundJob.query(BackgroundJob.deployment_key == dep.key,
                                   BackgroundJob.status == 1)
        params = {'jobs': jobs}
        self.render_smart_template('DEPLOYMENT',None,'background_job.html',dep,params)
