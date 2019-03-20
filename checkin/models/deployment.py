#!/usr/bin/env python
from globalconstants import *
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
from google.appengine.ext.webapp import blobstore_handlers
from random import randint
import unicodedata
from time import sleep
import csv
import StringIO
import json
from PyQRNativeGAE.PyQRNative import *
from PyQRNativeGAE.PyQRNativeGAE import *
from google.appengine.ext import deferred
from google.appengine.api import taskqueue
from google.appengine.runtime import DeadlineExceededError
from contextlib import closing
from zipfile import ZipFile, ZIP_DEFLATED
from google.appengine.api import urlfetch
import zipfile
import StringIO
from google.appengine.ext import deferred
from google.appengine.api import taskqueue
from google.appengine.runtime import DeadlineExceededError
from operator import itemgetter

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
    qr_codes_zip = ndb.BlobKeyProperty()
    qr_codes_zip_url = ndb.ComputedProperty(lambda self: self.get_qr_codes_url())
    student_link = ndb.TextProperty(indexed=True)
    student_link_text = ndb.TextProperty(indexed=True)
    user_link = ndb.TextProperty(indexed=True)
    user_link_text = ndb.TextProperty(indexed=True)
    max_visitor_serial_id = ndb.IntegerProperty(indexed=True)
    blocking_task_status = ndb.IntegerProperty()
    max_raffle_entries = ndb.IntegerProperty(indexed=True, default=0)

    def get_logo_url(self):
        if self.logo:
            return images.get_serving_url(self.logo, 1600, False, True)
        else:
            return ""

    def get_qr_codes_url(self):
        if self.qr_codes_zip is None:
            return ""

        try:
            if self.qr_codes_zip and blobstore.get(self.qr_codes_zip):
                return images.get_serving_url(self.qr_codes_zip)
            else:
                return ""
        except:
            return "http://check-me-in.biz/blobstore/images/" + str(self.qr_codes_zip)

    def get_sample_qr_code_url(self):
        try:
            if self.sample_qr_code and blobstore.get(self.sample_qr_code):
                return images.get_serving_url(self.sample_qr_code)
            else:
                return ""
        except:
            return "http://check-me-in.biz/blobstore/images/" + str(self.sample_qr_code)


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

    def upload_qr_code_zip(self,qr_code_zip,file_type):
        multipart_param = MultipartParam(
            'file', qr_code_zip, filename='qr_codes.zip', filetype=file_type)
        datagen, headers = multipart_encode([multipart_param])
        upload_url = blobstore.create_upload_url('/upload_image')

        result = urlfetch.fetch(
            url=upload_url,
            payload="".join(datagen),
            method=urlfetch.POST,
            headers=headers)

        blob = blobstore.get(json.loads(result.content)["key"])
        self.qr_codes_zip = blob.key()
        self.put()

    def upload_image_data(self,image_file):
        filetype = 'image/jpg'
        filename = 'test'

        multipart_param = MultipartParam(
            'file', image_file, filename=filename, filetype=filetype)
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

    def get_csv_reader(self,csv_file,should_sniff=True):
         file_stream = StringIO.StringIO(csv_file)
         if should_sniff:
              dialect = csv.Sniffer().sniff(file_stream.read(1024))
              file_stream.seek(0)
              has_headers = csv.Sniffer().has_header(file_stream.read(1024))
              file_stream.seek(0)
              reader = csv.reader(file_stream, dialect)
         else:
              reader = csv.reader(file_stream)
         return reader


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
