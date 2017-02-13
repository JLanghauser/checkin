from google.appengine.ext import ndb

class BackgroundJob (ndb.Model):
    user_key = ndb.KeyProperty(kind=User)
    deployment_key = ndb.KeyProperty(kind=Deployment)
    job_type = ndb.TextProperty(indexed=True)
    status = ndb.TextProperty(indexed=True)
    status_message = ndb.TextProperty(indexed=True)
    raw_data = ndb.BlobKeyProperty()
