from google.appengine.ext import ndb
from user import *
from deployment import *
from visitor import *

class MapUserToVisitor (ndb.Model):
    serialized_id = ndb.IntegerProperty(indexed=True)
    deployment_key = ndb.KeyProperty(kind=Deployment)
    user_key = ndb.KeyProperty(kind=User)
    visitor_key = ndb.KeyProperty(kind=Visitor)
    date_created = ndb.DateTimeProperty()
    category = ndb.ComputedProperty(lambda self: self.get_category())

    def get_category(self):
        user = self.user_key.get()
        if user:
            return user.category
        return None
