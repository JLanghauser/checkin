from google.appengine.ext import ndb
import webapp2
from handlers.visitors import *

app = webapp2.WSGIApplication([
    ('/tasks/update_visitor', VisitorSave)
], debug=True)
