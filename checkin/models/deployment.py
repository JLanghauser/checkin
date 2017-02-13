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
from visitor import *
from map_user_to_deployment import *
from map_user_to_visitor import *

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
    student_link = ndb.TextProperty(indexed=True)
    student_link_text = ndb.TextProperty(indexed=True)
    user_link = ndb.TextProperty(indexed=True)
    user_link_text = ndb.TextProperty(indexed=True)

    def get_logo_url(self):
        if self.logo:
            return images.get_serving_url(self.logo, 1600, False, True)
        else:
            return ""

    def get_sample_qr_code_url(self):
        if self.sample_qr_code:
            return images.get_serving_url(self.sample_qr_code, 1600, False, True)
        else:
            return ""

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

    def get_visitors(self):
        visitors = Visitor.query(Visitor.deployment_key == self.key)
        return visitors

    def get_users(self):
        qry2 = MapUserToDeployment.query(MapUserToDeployment.deployment_key == self.key)
        map_users_keys = qry2.fetch(projection=[MapUserToDeployment.user_key])
        users = {}
        # for mp in map_users_keys:
        #     u = mp.get()
        #     users.append(u)
        #users = ndb.get_multi(map_users_keys)
        #return users
        return users

    def get_random_visitor(self):
        entity_count = MapUserToVisitor.query(MapUserToVisitor.deployment_key == self.key).count()
        if (entity_count > 0):
            random_index = randint(0, entity_count - 1)
            maps = MapUserToVisitor.query(MapUserToVisitor.deployment_key == self.key).order(MapUserToVisitor.key).fetch()

            counter = 0
            for map_item in maps:
                if (random_index == counter):
                    key = map_item.visitor_key
                    rand_visitor = Visitor.get_by_id(
                        key.id(), parent=key.parent(), app=key.app(), namespace=key.namespace())
                    return rand_visitor.visitor_id
                counter = counter + 1
        return None

    def upload_qr_code(self,qrcodeimg,image_type):
        multipart_param = MultipartParam(
            'file', qrcodeimg, filename='sample_'+ self.slug, filetype=image_type)
        datagen, headers = multipart_encode([multipart_param])
        upload_url = blobstore.create_upload_url('/upload_image')

        result = urlfetch.fetch(
            url=upload_url,
            payload="".join(datagen),
            method=urlfetch.POST,
            headers=headers)

        blob = blobstore.get(json.loads(result.content)["key"])
        self.sample_qr_code = blob.key()
        self.put()

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
