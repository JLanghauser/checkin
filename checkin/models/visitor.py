from google.appengine.ext import ndb
from PyQRNativeGAE.PyQRNative import *
from PyQRNativeGAE.PyQRNativeGAE import *
from poster.encode import multipart_encode, MultipartParam
from poster.streaminghttp import register_openers
from google.appengine.api import images
from google.appengine.ext import db, ndb, blobstore
from google.appengine.api import urlfetch
from time import sleep
import csv
import StringIO
import json
from background_job import *
from google.appengine.runtime import DeadlineExceededError
from google.appengine.ext import deferred

class Visitor(ndb.Model):
    deployment_key = ndb.KeyProperty(kind=Deployment)
    serialized_id = ndb.IntegerProperty(indexed=True)
    visitor_id = ndb.TextProperty(indexed=True)
    qr_code = ndb.BlobKeyProperty()
    qr_code_url = ndb.ComputedProperty(lambda self: self.get_qr_code_url())
    checkin_url = ndb.TextProperty(indexed=True)
    or_progress = ndb.IntegerProperty(repeated=True, default=None)
    and_progress = ndb.IntegerProperty(repeated=True, default=None)

    def get_qr_code_url(self):
        try:
            if self.qr_code and blobstore.get(self.qr_code):
                return images.get_serving_url(self.qr_code)
            else:
                return ""
        except:
            return "http://check-me-in.biz/blobstore/images/" + str(self.qr_code)
