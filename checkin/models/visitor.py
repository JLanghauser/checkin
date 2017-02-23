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

class Deployment(ndb.Model):
    name = ndb.TextProperty(indexed=True)

class Visitor(ndb.Model):
    deployment_key = ndb.KeyProperty(kind=Deployment)
    serialized_id = ndb.IntegerProperty(indexed=True)
    visitor_id = ndb.TextProperty(indexed=True)
    qr_code = ndb.BlobKeyProperty()
    qr_code_url = ndb.ComputedProperty(lambda self: self.get_qr_code_url())
    checkin_url = ndb.TextProperty(indexed=True)

    def _pre_put_hook(self):
        self.set_qr_code();

    def get_qr_code_url(self):
        if self.qr_code and blobstore.get(self.qr_code):
            try:
                return images.get_serving_url(self.qr_code, 1600, False, True)
            except:
                return ""
        else:
            return ""

    def set_qr_code(self):
        newbackgroundjob = BackgroundJob()
        newbackgroundjob.deployment_key = self.deployment_key
        newbackgroundjob.status = 'CHILDPROCESS'
        newbackgroundjob.status_message = 'RUNNING - updating QR Code'
        newbackgroundjob.put()

        dep = self.deployment_key.get()
        url = dep.custom_subdomain + "." + dep.custom_dns + "/checkin_visitor?visitor_id=" +self.visitor_id
        self.checkin_url = url
        qr = QRCode(QRCode.get_type_for_string(url), QRErrorCorrectLevel.L)
        qr.addData(url)
        qr.make()
        img = qr.make_svg()
        self.upload_qr_code(img,"image/svg+xml")

        newbackgroundjob.status = 'PROCESSED'
        newbackgroundjob.put()

    def upload_qr_code(self,qrcodeimg,image_type,withput=False):
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
        self.qr_code = blob.key()
        if withput:
            self.put()
