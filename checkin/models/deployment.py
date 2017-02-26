#!/usr/bin/env python
from globalconstants import *
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
from PyQRNativeGAE.PyQRNative import *
from PyQRNativeGAE.PyQRNativeGAE import *
from background_job import *
from google.appengine.ext import deferred
from google.appengine.api import taskqueue
from google.appengine.runtime import DeadlineExceededError

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
    max_visitor_serial_id = ndb.IntegerProperty(indexed=True)

    def get_logo_url(self):
        if self.logo:
            return images.get_serving_url(self.logo, 1600, False, True)
        else:
            return ""

    def get_sample_qr_code_url(self):
        try:
            if self.sample_qr_code and blobstore.get(self.sample_qr_code):
                return images.get_serving_url(self.sample_qr_code)
            else:
                return ""
        except:
            return "/blobstore/images/" + str(self.sample_qr_code)

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
        visitors = Visitor.query(Visitor.deployment_key == self.key).order(Visitor.serialized_id)
        return visitors

    def get_users(self):
        qry2 = MapUserToDeployment.query(MapUserToDeployment.deployment_key == self.key)
        map_users_keys = qry2.fetch(projection=[MapUserToDeployment.user_key])
        users = []
        for mp in map_users_keys:
            u = mp.user_key.get()
            users.append(u)
        #users = ndb.get_multi(map_users_keys)
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

    def set_sample_qr_code(self):
        url = self.custom_subdomain + "." + self.custom_dns + "/checkin_visitor?visitor_id=9999999"
        qr = QRCode(QRCode.get_type_for_string(url), QRErrorCorrectLevel.L)
        qr.addData(url)
        qr.make()
        img = qr.make_svg()
        self.upload_qr_code(img,"image/svg+xml")
        sleep(0.5)

    def update_all_qr_codes(self,user):
        total_to_save = visitors = Visitor.query(Visitor.deployment_key == self.key).count()
        background_job = BackgroundJob.create_new(user.key,self.key,1)
        num_workers = NUM_BACKGROUND_JOB_WORKERS
        offset = 0

        for i in range(0,num_workers):
            if i == num_workers-1:
                 limit = int(total_to_save/num_workers) + total_to_save % num_workers
            else:
                 limit = int(total_to_save/num_workers)
            child = ChildProcess.create_new(background_job.key)
            deferred.defer(Visitor.updateqrcodes,self.key,child.key,offset,limit)
            offset = offset + int(total_to_save/num_workers)
            sleep(1)

        background_job.status = 1
        background_job.put()

    def upload_qr_code(self,qrcodeimg,image_type):
        multipart_param = MultipartParam(
            'file', qrcodeimg, filename='test-qr-code.svg', filetype=image_type)
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


    def generate_visitors(self,num_to_generate,user):
        background_job = BackgroundJob.create_new(user.key,self.key,0)
        num_workers = NUM_BACKGROUND_JOB_WORKERS
        start = self.max_visitor_serial_id
        if start:
            start = start + 1
        else:
            start = 1

        i = 0
        should_update = False
        while i < num_workers and should_update == False:
            if i == num_workers-1 or num_to_generate < num_workers:
                 end =  start + int(num_to_generate/num_workers) + num_to_generate % num_workers - 1
                 should_update = True
            else:
                 end = start + int(num_to_generate/num_workers) - 1
            child = ChildProcess.create_new(background_job.key)
            deferred.defer(Visitor.generate, self.key, child.key, start, end, should_update)
            start = end + 1
            i = i + 1
            sleep(1)

        background_job.status = 1
        background_job.put()

    def add_visitor(self, serialized_id, visitor_id):
        str_visitor_id = str(visitor_id)
        identical_object = Visitor.query(Visitor.deployment_key == self.key,
                            Visitor.visitor_id == str_visitor_id,
                            Visitor.serialized_id == serialized_id).get()

        same_serial = Visitor.query(Visitor.deployment_key == self.key,
                             Visitor.serialized_id == serialized_id).get()

        same_visitor = Visitor.query(Visitor.visitor_id == str_visitor_id,
                            Visitor.deployment_key == self.key).get()


        if same_visitor and not identical_object:
            return 1

        if same_serial and not identical_object:
            return 2

        if identical_object:
            return 3

        if visitor_id == 9999999:
            return 4

        newvisitor = Visitor()
        newvisitor.visitor_id = str_visitor_id
        newvisitor.serialized_id = serialized_id
        newvisitor.deployment_key = self.key
        newvisitor.set_qr_code()
        newvisitor.put()
        return 0


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

    def add_users_in_bulk(self,bulkfile):
        params = {}
        out_str = ''
        reader = None
        try:
            reader = self.get_csv_reader(bulkfile)

            count = 0
            skipped_header_row = False
            for row in reader:
                if not skipped_header_row:
                    skipped_header_row = True
                else:
                    retval = self.add_user(username=row[0], vendorname=row[2], password=row[3], is_deployment_admin=row[4], email=row[1])
                    count = count + 1
                    if retval is not "":
                        return retval
            return ""
        except csv.Error as e:
            if reader:
                return "File Error - line %d: %s" % (reader.line_num, e)
            else:
                return "Please verify file format - standard CSV with a header row."

        except:
            return "Unknown file error - please use a standard CSV with a header row."

    def add_user(self, username, vendorname, password, is_deployment_admin, email):
        tmp_user = User.get_by_username(username)

        if tmp_user:
            return "Error - user " + username + " already exists."
        else:
            if not username:
                return "Error - username cannot be blank."

            newuser = User()
            newuser.username = username
            newuser.vendorname = vendorname
            newuser.set_password(password)
            newuser.is_deployment_admin = is_deployment_admin in ['true', 'True', '1', 'on']
            newuser.profile = '<h1>Edit your profile <a href = "edit">here</a></h1>'
            newuser.email = email
            newuser.put()
            sleep(0.5)

            new_map = MapUserToDeployment()
            new_map.user_key = newuser.key
            new_map.deployment_key = self.key
            new_map.put()
            sleep(0.5)
            return ""

    def edit_user(self, old_username, new_username, vendorname, password, is_deployment_admin, email):
        edit_user = User.get_by_username(old_username)

        if edit_user:
            if not (new_username.lower() == old_username.lower()):
                tmp_user = User.get_by_username(new_username)

                if tmp_user:
                    return "Error - user " + new_username + " already exists."

                edit_user.username = new_username

            edit_user.vendorname = vendorname

            if (password != edit_user.password):
                edit_user.set_password(password)

            edit_user.is_deployment_admin = is_deployment_admin in [
                'true', 'True', '1', 'on']
            edit_user.email = email
            edit_user.put()

            maps = MapUserToDeployment.query(MapUserToDeployment.user_key == edit_user.key)
            for map in maps:
                map.key.delete()

            new_map = MapUserToDeployment()
            new_map.user_key = edit_user.key
            new_map.deployment_key = self.key
            new_map.put()
            sleep(0.5)
            return ""
        return "Could not find user"

    def delete_user(self,username):
        delete_user = User.get_by_username(username)

        maps = MapUserToDeployment.query(MapUserToDeployment.user_key == delete_user.key)
        for map in maps:
            map.key.delete()

        delete_user.key.delete()
        sleep(0.5)
        return ""

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
