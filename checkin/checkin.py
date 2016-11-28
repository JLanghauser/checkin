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
from time import sleep
import csv

class Deployment(ndb.Model):
    name = ndb.TextProperty(indexed=True)
    slug = ndb.TextProperty(indexed=True)
    custom_dns = ndb.TextProperty(indexed=True)
    custom_subdomain = ndb.TextProperty(indexed=True)

class MapUserToDeployment (ndb.Model):
    deployment_key = ndb.KeyProperty(kind=Deployment)
    user_key = ndb.KeyProperty(kind=User)

class Visitor(ndb.Model):
    deployment_key = ndb.KeyProperty(kind=Deployment)
    visitor_id = ndb.TextProperty(indexed=True)

class MapUserToVisitor (ndb.Model):
    deployment_key = ndb.KeyProperty(kind=Deployment)
    user_key = ndb.KeyProperty(kind=User)
    visitor_key = ndb.KeyProperty(kind=Visitor)

class ErrorPage(BaseHandler):
    def get(self):
        auth = self.auth
        self.render_template('error_page.html')

class MainPage(BaseHandler):
    def get(self):
        user = self.user
        if (user):
            params = {'userprofile': user.profile, 'user' : user}
            self.render_template('index.html',params)
        else:
            self.render_template('index.html')


class StudentHandler(BaseHandler):
    def handlerequest(self,deployment_slug):
        visitor_id = self.request.get('visitor_id','').strip()

        if (visitor_id == '' or not deployment_slug):
            self.render_template('error_page.html')
        else:
            deployment = Deployment.query(Deployment.slug == deployment_slug).get()
            if not deployment:
                self.render_template('error_page.html')

            qry = Visitor.query(Visitor.visitor_id == visitor_id,Visitor.deployment_key == deployment.key)
            visitor = qry.get()

            if (visitor):
                vkey = visitor.key
                maps = MapUserToVisitor.query(MapUserToVisitor.visitor_key == vkey).fetch()
                profiles = []
                for map_item in maps:
                    ukey = map_item.user_key
                    u = User.get_by_id(ukey.id(), parent=ukey.parent(), app=ukey.app(), namespace=ukey.namespace())
                    if ( "<h1>Edit your profile" in u.profile and  ">here</a></h1>" in u.profile and len(u.profile) < 60):
                        profiles.append("<h2>" + u.vendorname + "</h2>" + "<h3>This organization hasn't included any information)</h3>")
                    else:
                        profiles.append("<h2>" + u.vendorname + "</h2>" + u.profile)

                params = {'profiles': profiles}
                self.render_template('student.html',params)
            else:
                params = {'error': "true", 'flash_message' : "No such student " + visitor_id}
                self.render_template('studentlogin.html',params)

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
    def handlerequest(self,deployment_slug):
        visitor_id = self.request.get('visitor_id',-1)

        if (visitor_id == -1 or deployment_slug == ''):
            self.render_template('checkin_visitor.html')
        else:
            deployment = Deployment.query(Deployment.slug == deployment_slug).get()

            if not deployment:
                params = {'error': "true", 'flash_message' : "Cannot find deployment " + deployment_slug}
                self.render_template('checkin_visitor.html',params)

            new_map = MapUserToVisitor()
            new_map.user_key = self.user.key
            qry = Visitor.query(Visitor.visitor_id == visitor_id,Visitor.deployment_key == deployment.key)
            visitor = qry.get()
            if (visitor):
                maps = MapUserToVisitor.query(ndb.AND(
                            MapUserToVisitor.visitor_key == visitor.key,
                            MapUserToVisitor.user_key == self.user.key)
                        ).count(1)

                if (maps == 0):
                    new_map.visitor_key = visitor.key
                    new_map.deployment_key = visitor.deployment_key
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

class UsersHandler(BaseHandler):
    @deployment_admin_required
    def get(self):
        editing_username = self.request.get('editing_username','')
        users = User.query()
        params = {'users': users, 'editing_username' : editing_username}
        self.render_template('users_index.html',params)

    @deployment_admin_required
    def post(self):
        username = self.request.get('username')
        vendorname = self.request.get('vendorname')
        password = self.request.get('password')
        is_admin = self.request.get('admin')
        email = self.request.get('email')
        bulkfile = self.request.get('bulkfile')

        if bulkfile:
            params = {}
            out_str = ''
            try:
                #dialect = csv.Sniffer().sniff(bulkfile)
                #reader = csv.reader(bulkfile, dialect)
                reader = csv.reader(bulkfile)
                for row in reader:
                    print(', '.join(row))
            except csv.Error as e:
                params = {'error': "true", 'flash_message' : "File Error - line %d: %s" % (reader.line_num, e)}
            except:
                params = {'error': "true", 'flash_message' : "Unknown file error - please use a CSV"}

            self.render_template('users_index.html',params)
            return

        tmp_user = User.get_by_username(username)

        if tmp_user:
            self.render_template('error_page.html')
        else:
            if not username:
                params = {'error': "true", 'flash_message' : "username cannot be blank"}
                self.render_template('users_index.html',params)
                return

            newuser = User()
            newuser.username = username
            newuser.set_password(password)
            newuser.is_admin = is_admin in ['true', 'True', '1']
            newuser.profile = '<h1>Edit your profile <a href = "/edit">here</a></h1>'
            newuser.vendorname = vendorname
            newuser.email = email
            newuser.put()

            params = {'success': "true" , 'flash_message': "Successfully created User:  "  + newuser.username}
            self.render_template('users_.html',params)

class UserHandler(BaseHandler):
    @deployment_admin_required
    def post(self):
        self.render_template('error_page.html')

class VisitorListHandler(BaseHandler):
    @admin_required
    def get(self):
        self.render_template('error_page.html')

class VisitorHandler(BaseHandler):
    def handlerequest(self):
        visitor_id = self.request.get('visitor_id')

        qry = Visitor.query(Visitor.visitor_id == visitor_id)
        visitor = qry.get()
        if (visitor is None):
            newvisitor = Visitor()
            newvisitor.visitor_id = visitor_id
            newvisitor.put()
            params = {'success': "true" , 'flash_message': "Successfully created Visitor:  "  + newvisitor.visitor_id}
            self.render_template('index.html',params)
        else:
            params = {'error': "true" , 'flash_message': "Error - visitor "  + visitor_id  + " already exists!"}
            self.render_template('add_visitor.html',params)

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


class DeploymentsHandler(BaseHandler):
    @deployment_admin_required
    def get(self):
        editing_slug = self.request.get('editing_slug','')
        deployments = Deployment.query()
        params = {'deployments': deployments, 'editing_slug' : editing_slug}
        self.render_template('deployments_index.html',params)

    @super_admin_required
    def post(self):
        name = self.request.get('name')
        slug = self.request.get('slug')
        custom_dns = self.request.get('custom_dns')
        custom_subdomain = self.request.get('custom_subdomain')

        tmp_deployment = Deployment.query(Deployment.slug == slug).fetch(1)

        if tmp_deployment and len(tmp_deployment) :
            deployments = Deployment.query()
            params = {'error': "true" , 'flash_message': "Error - already exists!", 'deployments' : deployments}
            self.render_template('deployments_index.html',params)
        else:
            newdeployment = Deployment()
            newdeployment.name = name
            newdeployment.slug = slug
            newdeployment.custom_dns = custom_dns
            newdeployment.custom_subdomain = custom_subdomain
            newdeployment.put()

            sleep(0.5)
            deployments = Deployment.query()
            params = {'success': "true" , 'flash_message': "Successfully created Deployment:  "  + newdeployment.name, 'deployments' : deployments}
            self.render_template('deployments_index.html',params)

class DeploymentHandler(BaseHandler):
    @deployment_admin_required
    def post(self,deployment_slug):
        name = self.request.get('name')
        slug = self.request.get('slug')
        custom_dns = self.request.get('custom_dns')
        custom_subdomain = self.request.get('custom_subdomain')

        existing_deployment = Deployment.query(Deployment.slug == deployment_slug).fetch(1)
        if not existing_deployment or len(existing_deployment) < 1:
            params = {'error': "true" , 'flash_message': "Error - doesn't exist!"}
            self.render_template('deployments_index.html',params)
            return

        existing_deployment = existing_deployment[0]
        sleep(0.5)
        deployments = Deployment.query()
        params = {'success': "true" , 'flash_message': "Successfully update Deployment:  "  + existing_deployment.name, 'deployments' : deployments}
        self.render_template('deployments_index.html',params)


class MapUserToVisitorHandler(BaseHandler):
    @admin_required
    def get(self):
        self.response.out.write("MapUserToVisitorHandler get")


config = {
    'webapp2_extras.auth': {
        'user_model': 'auth_helpers.User',
        'user_attributes': ['username','email','is_super_admin', 'is_deployment_admin']
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
    webapp2.Route('/deployments', DeploymentsHandler, name='deployments'),
    webapp2.Route('/deployments/<deployment_slug>', DeploymentHandler, name='deployment'),
    webapp2.Route('/users', UsersHandler, name='users'),

    webapp2.Route('/<deployment_slug>/checkin_visitor', CheckInHandler, name='checkin'),
    webapp2.Route('/<deployment_slug>/student', StudentHandler, name='student'),
    webapp2.Route('/<deployment_slug>/admin_panel/user', UserHandler, name='new_user'),
    webapp2.Route('/<deployment_slug>/admin_panel/visitor', VisitorHandler, name='new_visitor'),
    webapp2.Route('/<deployment_slug>/admin_panel/visitors', VisitorListHandler, name='visitor_list'),
    webapp2.Route('/<deployment_slug>/admin_panel/get_random_visitor', RandomVisitorHandler, name='random_visitor'),
    webapp2.Route('/<deployment_slug>/admin_panel/get_all_map_user_to_visitors', MapUserToVisitorHandler, name='list_maps')
], config=config, debug=True)
