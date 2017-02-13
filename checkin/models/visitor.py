from google.appengine.ext import ndb

class Deployment(ndb.Model):
    name = ndb.TextProperty(indexed=True)
    
class Visitor(ndb.Model):
    deployment_key = ndb.KeyProperty(kind=Deployment)
    serialized_id = ndb.IntegerProperty(indexed=True)
    visitor_id = ndb.TextProperty(indexed=True)
