#!/usr/bin/env python
import cgi
import datetime
import webapp2
from array import *
from basehandler import *
from auth_helpers import *
from google.appengine.ext import ndb
from google.appengine.api import users
from random import randint
import unicodedata

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
        user = self.user
        params = {'userprofile': user.profile}
        self.render_template('index.html',params)


class StudentHandler(BaseHandler):
    def handlerequest(self):
        visitor_id = self.request.get('visitor_id','')
        if (visitor_id == ''):
            self.render_template('error_page.html')
        else:
            qry = Visitor.query(Visitor.visitor_id == visitor_id)
            visitor = qry.get()
            vkey = visitor.key
            maps = MapUserToVisitor.query(MapUserToVisitor.visitor_key == vkey).fetch()
            profiles = []

            for map_item in maps:
                ukey = map_item.user_key
                u = User.get_by_id(ukey.id(), parent=ukey.parent(), app=ukey.app(), namespace=ukey.namespace())
                profiles.append("<h2>" + u.vendorname + "</h2>" + u.profile)

            params = {'profiles': profiles}
            self.render_template('student.html',params)

    def get(self):
        visitor_id = self.request.get('visitor_id','')
        if (visitor_id == ''):
            self.render_template('studentlogin.html')
        else:
            self.handlerequest()

    def post(self):
        self.handlerequest()

class SignInHandler(BaseHandler):
    def handlerequest(self):
        raw_password = self.request.get('password')
        login = self.request.get('username')
        redirect_to = self.request.get('redirect_to','')
        tmp_user = User.get_by_username(login)

        if tmp_user:
            user_id = tmp_user.get_id()
            if security.check_password_hash(raw_password,tmp_user.password):
                self.auth.set_session(self.auth.store.user_to_dict(tmp_user))

                if (redirect_to != ''):
                    self.redirect(unicodedata.normalize('NFKD', redirect_to).encode('ascii','ignore'), abort=False)
                else:
                    self.redirect(self.uri_for('home'), abort=False)
            else:
                params = {'error': "true",'flash_message' : "Error signing in - please try again"}
                self.render_template('sign_in.html',params)

        else:
            params = {'error': "true",'flash_message' : "Error signing in - please try again"}
            self.render_template('sign_in.html',params)

    def get(self):
        raw_password = self.request.get('password','')
        login = self.request.get('username','')
        redirect_to = self.request.get('redirect_to','')

        if (raw_password != '' and login != ''):
            self.handlerequest()
        else:
            params = {'redirect_to': redirect_to}
            self.render_template('sign_in.html',params)

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
            user = self.user
            params = {'userprofile': user.profile}
            self.render_template('edit_user.html',params)
        else:
            self.user.profile = profile_param.strip()
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
                maps = MapUserToVisitor.query(ndb.AND(
                            MapUserToVisitor.visitor_key == visitor.key,
                            MapUserToVisitor.user_key == self.user.key)
                        ).count(1)

                if (maps == 0):
                    new_map.visitor_key = visitor.key
                    new_map.put()
                    params = {'visitor_id': visitor_id}
                    self.render_template('successful_checkin.html',params)
                else:
                    params = {'error': "true", 'flash_message' : "You've already checked in visitor " + visitor_id}
                    self.render_template('checkin_visitor.html',params)
            else:
                params = {'error': "true", 'flash_message' : "Cannot find visitor " + visitor_id}
                self.render_template('checkin_visitor.html',params)

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
        vendorname = self.request.get('vendorname')
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
            newuser.is_admin = is_admin in ['true', 'True', '1']
            newuser.profile = '<h1>Edit your profile <a href = "/edit">here</a></h1>'
            newuser.vendorname = vendorname
            newuser.email = email
            newuser.put()

            params = {'success': "true" , 'flash_message': "Successfully created User:  "  + newuser.username}
            self.render_template('index.html',params)

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
        'user_attributes': ['username','email','is_admin']
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
    webapp2.Route('/student', StudentHandler, name='student'),
    webapp2.Route('/admin_panel/users', UserListHandler, name='user_list'),
    webapp2.Route('/admin_panel/user', UserHandler, name='new_user'),
    webapp2.Route('/admin_panel/visitor', VisitorHandler, name='new_visitor'),
    webapp2.Route('/admin_panel/visitors', VisitorListHandler, name='visitor_list'),
    webapp2.Route('/admin_panel/get_random_visitor', RandomVisitorHandler, name='random_visitor'),
    webapp2.Route('/admin_panel/get_all_map_user_to_visitors', MapUserToVisitorHandler, name='list_maps')
], config=config, debug=True)
