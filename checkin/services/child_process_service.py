from poster.encode import multipart_encode, MultipartParam
from google.appengine.ext import db, ndb, blobstore
from google.appengine.api import urlfetch
import json
from models.visitor import *
from models.background_job import *
from services.background_job_service import *
from services.visitor_service import *

class ChildProcessService:
    @staticmethod
    def create_new(background_job_key):
        newprocess = ChildProcess()
        newprocess.background_job_key = background_job_key
        newprocess.put()
        return newprocess

    @staticmethod
    def update_all_qr_codes(deployment,user):
        total_to_save = visitors = Visitor.query(Visitor.deployment_key == deployment.key).count()

        if total_to_save > 0:
            background_job = BackgroundJobService.create_new(user.key,deployment.key,1)
            num_workers = NUM_BACKGROUND_JOB_WORKERS
            offset = 0

            for i in range(0,num_workers):
                if i == num_workers-1:
                     limit = int(total_to_save/num_workers) + total_to_save % num_workers
                else:
                     limit = int(total_to_save/num_workers)
                child = ChildProcessService.create_new(background_job.key)
                deferred.defer(VisitorService.updateqrcodes,deployment.key,child.key,offset,limit)
                offset = offset + int(total_to_save/num_workers)
                sleep(1)

            background_job.status = 1
            background_job.put()

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
