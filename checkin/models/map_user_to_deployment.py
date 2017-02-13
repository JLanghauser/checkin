from google.appengine.ext import ndb
from deployment import *
from user import *

class MapUserToDeployment (ndb.Model):
    deployment_key = ndb.KeyProperty(kind=Deployment)
    user_key = ndb.KeyProperty(kind=User)
