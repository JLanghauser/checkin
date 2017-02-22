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
from PyQRNativeGAE.PyQRNative import *
from PyQRNativeGAE.PyQRNativeGAE import *
from background_job import *

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
        if self.sample_qr_code and blobstore.get(self.sample_qr_code):
            try:
                return images.get_serving_url(self.sample_qr_code, 1600, False, True)
            except:
                return ""
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

    def update_all_qr_codes(self):
        newbackgroundjob = BackgroundJob()
        newbackgroundjob.deployment_key = self.key
        newbackgroundjob.status = 'INPROGRESS'
        newbackgroundjob.status_message = 'RUNNING - updating QR codes for all visitors...'
        newbackgroundjob.put()

        visitors = Visitor.query(Visitor.deployment_key == self.key)
        for visitor in visitors:
            visitor.put()

        newbackgroundjob.status = 'COMPLETED'
        newbackgroundjob.put()
        sleep(0.5)

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

    def generate_serial_id(self):
        starting_id = 0
        if self.max_visitor_serial_id:
            starting_id = self.max_visitor_serial_id
        serialized_id = starting_id + 1
        return serialized_id

    def generate_visitor_id(self):
        visitor_id = ""
        for x in range(0,6):
            rand_val = str(randint(0, 9))
            if x == 0:
                while rand_val == '0':
                    rand_val = str(randint(0, 9))
            visitor_id += rand_val
        return visitor_id

    def generate_visitors(self,num_to_generate):
        newbackgroundjob = BackgroundJob()
        newbackgroundjob.deployment_key = self.key
        newbackgroundjob.status = 'INPROGRESS'
        newbackgroundjob.status_message = 'RUNNING - generating ' + num_to_generate + ' qrcodes...'
        newbackgroundjob.put()

        starting_id = 0
        for i in range(0,int(num_to_generate)):
            serialized_id = self.generate_serial_id()
            visitor_id = self.generate_visitor_id()
            retval = 'START'
            while retval != '':
                retval = self.add_visitor(serialized_id,int(visitor_id))
            self.max_visitor_serial_id = serialized_id
            self.put()

        newbackgroundjob.status = 'COMPLETED'
        newbackgroundjob.put()
        sleep(0.5)

    def add_visitor(self, serialized_id, visitor_id):
        str_visitor_id = str(visitor_id)
        qry = Visitor.query(Visitor.visitor_id == str_visitor_id,
                            Visitor.serialized_id == serialized_id,
                            Visitor.deployment_key == self.key)

        qry2 = Visitor.query(Visitor.serialized_id == serialized_id,
                            Visitor.deployment_key == self.key)

        total_visitor = qry.get()
        serial_visitor = qry2.get()

        if (total_visitor is None and visitor_id != 9999999
            and visitor_id != 0 and serial_visitor is None):
            newvisitor = Visitor()
            newvisitor.visitor_id = str_visitor_id
            newvisitor.serialized_id = serialized_id
            newvisitor.deployment_key = self.key
            newvisitor.put()
            return ""
        else:
            max_id = self.max_visitor_serial_id
            if total_visitor and total_visitor.serialized_id > max_id:
                max_id = total_visitor.serialized_id

            if serial_visitor and serial_visitor.serialized_id > max_id:
                max_id = serial_visitor.serialized_id

            if max_id > self.max_visitor_serial_id:
                self.max_visitor_serial_id = max_id
                self.put()
            return "Error - Bad User"

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
