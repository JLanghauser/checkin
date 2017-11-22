from models.deployment import *
from models.user import *
from models.visitor import *
from services.background_job_service import *
from services.child_process_service import *
from services.visitor_service import *

class GeneratorService:
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
