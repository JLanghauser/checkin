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

class Deployment(ndb.Model):
    name = ndb.TextProperty(indexed=True)

class Visitor(ndb.Model):
    deployment_key = ndb.KeyProperty(kind=Deployment)
    serialized_id = ndb.IntegerProperty(indexed=True)
    visitor_id = ndb.TextProperty(indexed=True)
    qr_code = ndb.BlobKeyProperty()
    qr_code_url = ndb.ComputedProperty(lambda self: self.get_qr_code_url())

    def _pre_put_hook(self):
        self.set_qr_code();

    def get_qr_code_url(self):
        if self.qr_code:
            return images.get_serving_url(self.qr_code, 1600, False, True)
        else:
            return ""

    def set_qr_code(self):
        dep = self.deployment_key.get()
        url = dep.custom_subdomain + "." + dep.custom_dns + "/checkin_visitor?visitor_id=" +self.visitor_id
        qr = QRCode(QRCode.get_type_for_string(url), QRErrorCorrectLevel.L)
        qr.addData(url)
        qr.make()
        img = qr.make_svg()
        self.upload_qr_code(img,"image/svg+xml")

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
