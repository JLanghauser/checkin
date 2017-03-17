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

class Deployment(ndb.Model):
    name = ndb.TextProperty(indexed=True)

class Visitor(ndb.Model):
    deployment_key = ndb.KeyProperty(kind=Deployment)
    serialized_id = ndb.IntegerProperty(indexed=True)
    visitor_id = ndb.TextProperty(indexed=True)
    qr_code = ndb.BlobKeyProperty()
    qr_code_url = ndb.ComputedProperty(lambda self: self.get_qr_code_url())
    checkin_url = ndb.TextProperty(indexed=True)

    def get_qr_code_url(self):
        try:
            if self.qr_code and blobstore.get(self.qr_code):
                return images.get_serving_url(self.qr_code)
            else:
                return ""
        except:
            return "http://check-me-in.biz/blobstore/images/" + str(self.qr_code)

    def set_qr_code(self,withput=False):
        dep = self.deployment_key.get()
        if dep.custom_subdomain and dep.custom_dns:
            url = dep.custom_subdomain + "." + dep.custom_dns + "/checkin_visitor?visitor_id=" +self.visitor_id
            self.checkin_url = url
            qr = QRCode(QRCode.get_type_for_string(url), QRErrorCorrectLevel.L)
            qr.addData(url)
            qr.make()
            img = qr.make_image()
            self.upload_qr_code(img,"image/png",withput=withput)

    def upload_qr_code(self,qrcodeimg,image_type,withput=False):
        multipart_param = MultipartParam(
            'file', qrcodeimg, filename='test-qr-code.png', filetype=image_type)
        datagen, headers = multipart_encode([multipart_param])
        upload_url = blobstore.create_upload_url('/upload_image')

        result = urlfetch.fetch(
            url=upload_url,
            payload="".join(datagen),
            method=urlfetch.POST,
            headers=headers)

        blob = blobstore.get(json.loads(result.content)["key"])
        self.qr_code = blob.key()
        if withput:
            self.put()

    @classmethod
    def updateqrcodes(cls,dep_key,child_key,offset,limit):
        current_offset = offset
        current_limit = limit
        child = None
        try:
            child = child_key.get()
            dep = dep_key.get()

            if limit > 0:
                visitors = Visitor.query(Visitor.deployment_key == dep.key)\
                                    .order(Visitor.serialized_id)\
                                    .fetch(offset=offset,limit=limit)

                for visitor in visitors:
                    visitor.set_qr_code(withput=True)
                    current_offset = current_offset + 1
                    current_limit = current_limit - 1

            if child:
                child.key.delete()
                child = None
        except DeadlineExceededError:
            deferred.defer(Visitor.updateqrcodes,dep_key,child_key,current_offset,current_limit)

    @classmethod
    def generate(cls,dep_key,child_key,start_id,end_id,should_update_deployment):
        start = start_id
        child = None
        try:
            child = child_key.get()
            dep = dep_key.get()
            start = start_id
            for start in range(start_id,end_id+1):
                retval = 1
                while retval == 1 or retval == 3 or retval == 4:
                    visitor_id = Visitor.generate_visitor_id()
                    retval = dep.add_visitor(start,int(visitor_id))
            if should_update_deployment == True:
                dep.max_visitor_serial_id = end_id
                dep.put()
            if child:
                child.key.delete()
                child = None
        except DeadlineExceededError:
            deferred.defer(cls.generate,dep_key,child_key,start,end_id,should_update_deployment)

    # @classmethod
    # def generate_serial_id(cls,seed):
    #     starting_id = seed
    #     if self.max_visitor_serial_id and self.max_visitor_serial_id > starting_id:
    #         starting_id = self.max_visitor_serial_id
    #     serialized_id = starting_id + 1
    #     return serialized_id

    @classmethod
    def generate_visitor_id(cls):
        visitor_id = ""
        for x in range(0,6):
            rand_val = str(randint(0, 9))
            if x == 0:
                while rand_val == '0':
                    rand_val = str(randint(0, 9))
            visitor_id += rand_val
        return visitor_id
