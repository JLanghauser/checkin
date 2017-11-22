from poster.encode import multipart_encode, MultipartParam
from google.appengine.ext import db, ndb, blobstore
from google.appengine.api import urlfetch
import json
from models.visitor import *
from models.background_job import *
from services.background_job_service import *

class ChildProcessService:
    @staticmethod
    def create_new(background_job_key):
        newprocess = ChildProcess()
        newprocess.background_job_key = background_job_key
        newprocess.put()
        return newprocess

    @staticmethod
    def upload_qr_code(deployment,qrcodeimg,image_type):
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
        deployment.sample_qr_code = blob.key()
        deployment.put()
