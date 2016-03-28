#!/usr/bin/env python
import cgi
import datetime
import webapp2
from basehandler import *
from auth_helpers import *
from google.appengine.ext import ndb
from google.appengine.api import users

guestbook_key = ndb.Key('Guestbook', 'default_guestbook')

class Visitor(ndb.Model):
    visitor_id = ndb.TextProperty(indexed=True)

class MapUserToVisitor (ndb.Model):
    user_key = ndb.KeyProperty(kind=User)
    visitor_key = ndb.KeyProperty(kind=Visitor)

class MainPage(BaseHandler):

    def get(self):
        self.response.out.write('<html><body>')
        auth = self.auth
        if auth.get_user_by_session():
            self.response.out.write("""
              <h1> You're logged in! :-)</h1>
            </body>
          </html>""")
        else:
            self.response.out.write("""
              <h1> You're not logged in! :-()</h1>
            </body>
          </html>""")



class SignInHandler(BaseHandler):

    def get(self):
        self.render_template('sign_in.html')

    def post(self):
        raw_password = self.request.get('password')
        login = self.request.get('username')
        tmp_user = User.get_by_username(login)

        if tmp_user:
            user_id = tmp_user.get_id()

            if security.check_password_hash(raw_password,tmp_user.password):
                self.auth.set_session(self.auth.store.user_to_dict(tmp_user))
                self.render_template('success_page.html')
            else:
                self.render_template('error_page.html')

        else:
            self.render_template('error_page.html')


class SignOutHandler(BaseHandler):

    def get(self):
        self.auth.unset_session();
        self.render_template('success_page.html')

    def post(self):
        self.auth.unset_session();
        self.render_template('success_page.html')


class CheckInHandler(BaseHandler):

    def get(self):
        auth = self.auth
        if auth.get_user_by_session():
            self.render_template('checkin_visitor.html')
        else:
            # remember URL in cookie
            self.render_template('sign_in.html')

    def post(self):
        visitor_id = self.request.get('visitor_id')
        new_map = MapUserToVisitor()
        new_map.user_key = self.auth.get_user_by_session().key
        qry = Visitor.query(Visitor.visitor_id == visitor_id)
        visitor = qry.get()
        if (visitor):
            new_map.visitor_key = visitor.key
            new_map.put()
        else:
            self.render_template('error_page.html')
        self.render_template('success_page.html')


class UserListHandler(BaseHandler):
    def get(self):
        self.render_template('list_users.html')

class UserHandler(BaseHandler):
    def get(self):
        self.render_template('add_user.html')

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')
        is_admin = self.request.get('admin')
        email = self.request.get('email')

        tmp_user = User.get_by_username(username)

        if tmp_user:
            self.render_template('error_page.html')
        else:
            newuser = User()
            newuser.username = username
            newuser.set_password(password)
            newuser.admin = is_admin
            newuser.email = email
            newuser.put()

        self.render_template('success_page.html')

class VisitorListHandler(BaseHandler):
    def get(self):
        self.render_template('error_page.html')

    def post(self):
        self.render_template('error_page.html')

class VisitorHandler(BaseHandler):

    def get(self):
        self.render_template('add_visitor.html')

    def post(self):
        newvisitor = Visitor()
        newvisitor.visitor_id = self.request.get('visitor_id')
        newvisitor.put()
        self.render_template('success_page.html')


class RandomVisitorHandler(BaseHandler):

    def get(self):
        self.response.out.write("RandomVisitorHandler get")

    def post(self):
        self.response.out.write("RandomVisitorHandler post")


class MapUserToVisitorHandler(BaseHandler):

    def get(self):
        self.response.out.write("MapUserToVisitorHandler get")

    def post(self):
        self.response.out.write("MapUserToVisitorHandler post")

config = {
    'webapp2_extras.auth': {
        'user_model': 'auth_helpers.User',
        'user_attributes': ['username']
    },
    'webapp2_extras.sessions': {
        'secret_key': 'YOUR_SECRET_KEY'
    }
}

app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/sign_in', SignInHandler),
    ('/sign_out', SignOutHandler),
    ('/checkin_visitor', CheckInHandler),
    ('/admin/users', UserListHandler),
    ('/admin/user', UserHandler),
    ('/admin/visitor', VisitorHandler),
    ('/admin/visitors', VisitorListHandler),
    ('/admin/get_random_visitor', RandomVisitorHandler),
    ('/admin/get_all_map_user_to_visitors', MapUserToVisitorHandler),
], config=config, debug=True)
