from google.appengine.ext import ndb
from deployment import *
from user import *

class MapUserToDeployment (ndb.Model):
    deployment_key = ndb.KeyProperty(kind=Deployment,indexed=True)
    user_key = ndb.KeyProperty(kind=User,indexed=True)
