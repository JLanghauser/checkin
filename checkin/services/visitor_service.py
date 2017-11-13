from models.deployment import *
from models.user import *
from models.visitor import *
from services.background_job_service import *
from services.child_process_service import *

class VisitorService:

    @staticmethod
    def set_qr_code(visitor,withput=False):
        dep = visitor.deployment_key.get()
        if dep.custom_subdomain and dep.custom_dns:
            url = dep.custom_subdomain + "." + dep.custom_dns + "/checkin_visitor?visitor_id=" + visitor.visitor_id
            visitor.checkin_url = url
            qr = QRCode(QRCode.get_type_for_string(url), QRErrorCorrectLevel.L)
            qr.addData(url)
            qr.make()
            img = qr.make_image()
            VisitorService.upload_qr_code(visitor, img,"image/png",withput=withput)
            visitor.put()

    @staticmethod
    def upload_qr_code(visitor,qrcodeimg,image_type,withput=False):
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
        visitor.qr_code = blob.key()
        if withput:
            visitor.put()

    @staticmethod
    def updateqrcodes(dep_key,child_key,offset,limit):
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
                    visitor_id = VisitorService.generate_visitor_id()
                    retval = VisitorService.add_visitor(dep,start,int(visitor_id))
            if should_update_deployment == True:
                dep.max_visitor_serial_id = end_id
                dep.put()
            if child:
                child.key.delete()
                child = None
        except DeadlineExceededError:
            deferred.defer(VisitorService.generate,dep_key,child_key,start,end_id,should_update_deployment)


    @staticmethod
    def add_visitor(deployment, serialized_id, visitor_id):
        str_visitor_id = str(visitor_id)
        identical_object = Visitor.query(Visitor.deployment_key == deployment.key,
                            Visitor.visitor_id == str_visitor_id,
                            Visitor.serialized_id == serialized_id).get()

        same_serial = Visitor.query(Visitor.deployment_key == deployment.key,
                             Visitor.serialized_id == serialized_id).get()

        same_visitor = Visitor.query(Visitor.visitor_id == str_visitor_id,
                            Visitor.deployment_key == deployment.key).get()


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
        newvisitor.deployment_key = deployment.key
        newvisitor.put()
        VisitorService.set_qr_code(newvisitor)
        return 0

    @staticmethod
    def generate_visitors(deployment,num_to_generate,user,start_at_one=None):
        background_job = BackgroundJobService.create_new(user.key,deployment.key,0)
        num_workers = NUM_BACKGROUND_JOB_WORKERS
        start = deployment.max_visitor_serial_id
        if start:
            start = start + 1
        else:
            start = 1

        if start_at_one:
            start = 1

        i = 0
        should_update = False
        while i < num_workers and should_update == False:
            if i == num_workers-1 or num_to_generate < num_workers:
                 end =  start + int(num_to_generate/num_workers) + num_to_generate % num_workers - 1
                 should_update = True
            else:
                 end = start + int(num_to_generate/num_workers) - 1
            child = ChildProcessService.create_new(background_job.key)
            deferred.defer(VisitorService.generate, deployment.key, child.key, start, end, should_update)
            start = end + 1
            i = i + 1
            sleep(1)

        background_job.status = 1
        background_job.put()

    # @classmethod
    # def generate_serial_id(cls,seed):
    #     starting_id = seed
    #     if self.max_visitor_serial_id and self.max_visitor_serial_id > starting_id:
    #         starting_id = self.max_visitor_serial_id
    #     serialized_id = starting_id + 1
    #     return serialized_id

    @staticmethod
    def generate_visitor_id():
        visitor_id = ""
        for x in range(0,6):
            rand_val = str(randint(0, 9))
            if x == 0:
                while rand_val == '0':
                    rand_val = str(randint(0, 9))
            visitor_id += rand_val
        return visitor_id
