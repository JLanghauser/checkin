from google.appengine.ext import ndb
from user import *
from deployment import *

class MapUserToVisitor (ndb.Model):
    deployment_key = ndb.KeyProperty(kind=Deployment)
    user_key = ndb.KeyProperty(kind=User)
    visitor_key = ndb.KeyProperty(kind=Visitor)
    date_created = ndb.DateTimeProperty()
