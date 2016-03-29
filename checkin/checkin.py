#!/usr/bin/env python
import cgi
import datetime
import webapp2
from basehandler import *
from auth_helpers import *
from google.appengine.ext import ndb
from google.appengine.api import users
from random import randint


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


class CheckInHandler(BaseHandler):
    def handlerequest(self):
        visitor_id = self.request.get('visitor_id',-1)
        if (visitor_id == -1):
            self.render_template('checkin_visitor.html')
        else:
            new_map = MapUserToVisitor()
            new_map.user_key = self.user.key
            qry = Visitor.query(Visitor.visitor_id == visitor_id)
            visitor = qry.get()
            if (visitor):
                new_map.visitor_key = visitor.key
                new_map.put()
            else:
                self.render_template('error_page.html')
            self.render_template('success_page.html')

    @user_required
    def get(self):
        self.handlerequest()

    @user_required
    def post(self):
        self.handlerequest()

class UserListHandler(BaseHandler):
    @admin_required
    def get(self):
        self.render_template('list_users.html')

class UserHandler(BaseHandler):
    @admin_required
    def get(self):
        self.render_template('add_user.html')

    @admin_required
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
    @admin_required
    def get(self):
        self.render_template('error_page.html')

class VisitorHandler(BaseHandler):
    @admin_required
    def get(self):
        self.render_template('add_visitor.html')

    @admin_required
    def post(self):
        newvisitor = Visitor()
        newvisitor.visitor_id = self.request.get('visitor_id')
        newvisitor.put()
        self.render_template('success_page.html')


class RandomVisitorHandler(BaseHandler):
    @admin_required
    def get(self):
        # get count
        entity_count = MapUserToVisitor.query().count()

        # get random number
        random_index = randint(0,entity_count-1)

        # Get all the keys, not the Entities
        maps = MapUserToVisitor.query().order(MapUserToVisitor.key).fetch()

        counter = 0
        for map_item in maps:
            if (random_index == counter):
                key = map_item.visitor_key
                rand_visitor = Visitor.get_by_id(key.id(), parent=key.parent(), app=key.app(), namespace=key.namespace())
                self.response.out.write("And the winner is... " + rand_visitor.visitor_id)
            counter = counter + 1



class MapUserToVisitorHandler(BaseHandler):
    @admin_required
    def get(self):
        self.response.out.write("MapUserToVisitorHandler get")


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
    webapp2.Route('/', MainPage, name='home'),
    webapp2.Route('/sign_in', SignInHandler, name='sign_in'),
    webapp2.Route('/sign_out', SignOutHandler, name='sign_out'),
    webapp2.Route('/checkin_visitor', CheckInHandler, name='checkin'),
    webapp2.Route('/admin/users', UserListHandler, name='user_list'),
    webapp2.Route('/admin/user', UserHandler, name='new_user'),
    webapp2.Route('/admin/visitor', VisitorHandler, name='new_visitor'),
    webapp2.Route('/admin/visitors', VisitorListHandler, name='visitor_list'),
    webapp2.Route('/admin/get_random_visitor', RandomVisitorHandler, name='random_visitor'),
    webapp2.Route('/admin/get_all_map_user_to_visitors', MapUserToVisitorHandler, name='list_maps')
], config=config, debug=True)
