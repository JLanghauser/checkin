#!/usr/bin/env python
import cgi
import datetime
import webapp2
from basehandler import *
from auth_helpers import *
from google.appengine.ext import ndb
from google.appengine.api import users
from random import randint

class Visitor(ndb.Model):
    visitor_id = ndb.TextProperty(indexed=True)

class MapUserToVisitor (ndb.Model):
    user_key = ndb.KeyProperty(kind=User)
    visitor_key = ndb.KeyProperty(kind=Visitor)

class ErrorPage(BaseHandler):
    def get(self):
        auth = self.auth
        self.render_template('error_page.html')

class MainPage(BaseHandler):
    def get(self):
        auth = self.auth
        self.render_template('index.html')


class StudentsHandler(BaseHandler):
    def handlerequest(self):
        visitor_id = self.request.get('visitor_id','')
        self.render_template('students.html')

    def get(self):
        visitor_id = self.request.get('visitor_id','')
        if (visitor_id == ''):
            self.render_template('studentlogin.html')
        else:
            self.render_template('students.html')

    def post(self):
        self.handlerequest()

class SignInHandler(BaseHandler):
    def handlerequest(self):
        raw_password = self.request.get('password')
        login = self.request.get('username')
        tmp_user = User.get_by_username(login)

        if tmp_user:
            user_id = tmp_user.get_id()

            if security.check_password_hash(raw_password,tmp_user.password):
                self.auth.set_session(self.auth.store.user_to_dict(tmp_user))
                self.redirect(self.uri_for('home'), abort=False)
            else:
                self.render_template('error_page.html')

        else:
            self.render_template('error_page.html')

    def get(self):
        raw_password = self.request.get('password','')
        login = self.request.get('username','')

        if (raw_password != '' and login != ''):
            self.handlerequest()
        else:
            self.render_template('sign_in.html')

    def post(self):
        self.handlerequest()

class SignOutHandler(BaseHandler):
    def get(self):
        self.auth.unset_session();
        self.redirect(self.uri_for('home'), abort=False)

class UserEditHandler(BaseHandler):
    def handlerequest(self):
        profile_param = self.request.get('profile',-1)
        if (profile_param == -1):
            self.render_template('edit_user.html')
        else:
            self.user.profile = profile_param
            self.user.put()
            tmpuser = self.user
            self.auth.unset_session();
            self.auth.set_session(self.auth.store.user_to_dict(tmpuser))
            self.redirect(self.uri_for('home'), abort=False)

    @user_required
    def get(self):
        self.handlerequest()

    @user_required
    def post(self):
        self.handlerequest()

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
                params = {'visitor_id': visitor_id}
                self.render_template('successful_checkin.html',params)
            else:
                self.render_template('error_page.html')

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
            newuser.is_admin = is_admin
            newuser.profile = 'Put some bio information here'
            newuser.email = email
            newuser.put()

        self.render_template('success_page.html')

class VisitorListHandler(BaseHandler):
    @admin_required
    def get(self):
        self.render_template('error_page.html')

class VisitorHandler(BaseHandler):
    def handlerequest(self):
        newvisitor = Visitor()
        newvisitor.visitor_id = self.request.get('visitor_id')
        newvisitor.put()
        self.render_template('success_page.html')

    @admin_required
    def get(self):
        visitor_id = self.request.get('visitor_id',-1)
        if (visitor_id == -1):
            self.render_template('add_visitor.html')
        else:
            self.handlerequest()

    @admin_required
    def post(self):
        self.handlerequest();


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
                params = {'visitor_id': rand_visitor.visitor_id}
                self.render_template('raffle_results.html',params)
                return
            counter = counter + 1


class MapUserToVisitorHandler(BaseHandler):
    @admin_required
    def get(self):
        self.response.out.write("MapUserToVisitorHandler get")


config = {
    'webapp2_extras.auth': {
        'user_model': 'auth_helpers.User',
        'user_attributes': ['username','email','profile']
    },
    'webapp2_extras.sessions': {
        'secret_key': 'YOUR_SECRET_KEY'
    }
}

app = webapp2.WSGIApplication([
    webapp2.Route('/', MainPage, name='home'),
    webapp2.Route('/error', ErrorPage, name='error'),
    webapp2.Route('/sign_in', SignInHandler, name='sign_in'),
    webapp2.Route('/sign_out', SignOutHandler, name='sign_out'),
    webapp2.Route('/edit', UserEditHandler, name='edit'),
    webapp2.Route('/checkin_visitor', CheckInHandler, name='checkin'),
    webapp2.Route('/students', StudentsHandler, name='students'),
    webapp2.Route('/admin_panel/users', UserListHandler, name='user_list'),
    webapp2.Route('/admin_panel/user', UserHandler, name='new_user'),
    webapp2.Route('/admin_panel/visitor', VisitorHandler, name='new_visitor'),
    webapp2.Route('/admin_panel/visitors', VisitorListHandler, name='visitor_list'),
    webapp2.Route('/admin_panel/get_random_visitor', RandomVisitorHandler, name='random_visitor'),
    webapp2.Route('/admin_panel/get_all_map_user_to_visitors', MapUserToVisitorHandler, name='list_maps')
], config=config, debug=True)
