#!/usr/bin/env python
import cgi
import datetime
import webapp2
from array import *
from basehandler import *
from auth_helpers import *
from google.appengine.ext import ndb
from google.appengine.api import users
from google.appengine.ext.webapp import blobstore_handlers
from random import randint
import unicodedata
from time import sleep
import csv
import StringIO
import json

class MapUserToDeployment (ndb.Model):
    deployment_key = ndb.KeyProperty(kind=Deployment)
    user_key = ndb.KeyProperty(kind=User)

class Visitor(ndb.Model):
    deployment_key = ndb.KeyProperty(kind=Deployment)
    visitor_id = ndb.TextProperty(indexed=True)

class MapUserToVisitor (ndb.Model):
    deployment_key = ndb.KeyProperty(kind=Deployment)
    user_key = ndb.KeyProperty(kind=User)
    visitor_key = ndb.KeyProperty(kind=Visitor)
