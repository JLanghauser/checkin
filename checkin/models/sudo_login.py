from google.appengine.ext import ndb
from user import *

class SudoLogin (ndb.Model):
    admin_key = ndb.KeyProperty(kind=User)
    user_key = ndb.KeyProperty(kind=User)
