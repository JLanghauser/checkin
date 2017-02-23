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
        jobs = BackgroundJob.query(BackgroundJob.deployment_key == dep.key,BackgroundJob.status.IN(['INPROGRESS', 'COMPLETED']))
        for job in jobs:
            if job.status == 'COMPLETED':
                job.status_message = job.status_message.replace('RUNNING','FINISHED')
                job.status='PROCESSED'
                job.put()
            elif 'updating QR codes for all visitors' in job.status_message:
                remaining = BackgroundJob.query(BackgroundJob.deployment_key == dep.key,BackgroundJob.status == 'CHILDPROCESS').count()
                mins =  int(round(.5*remaining))
                secs =  abs(int(round(30*remaining)) - mins*60)
                job.status_message = 'RUNNING - updating QR codes for all visitors:  ~' + str(mins) + ' minutes, ' +  str(secs) + ' seconds remaining...'
                job.put()

        params = {'jobs': jobs}
        self.render_smart_template('DEPLOYMENT',None,'background_job.html',dep,params)
