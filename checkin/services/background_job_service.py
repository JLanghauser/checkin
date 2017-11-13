from models.background_job import *

class BackgroundJobService:
    @classmethod
    def create_new(cls, user_key, deployment_key, job_type):
        newjob = BackgroundJob()
        newjob.user_key = user_key
        newjob.deployment_key = deployment_key
        newjob.job_type = job_type
        newjob.status = 0
        newjob.put()
        return newjob
