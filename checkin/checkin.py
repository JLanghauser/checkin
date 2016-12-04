#!/usr/bin/env python
import cgi
import datetime
import webapp2
from array import *
from basehandler import *
from auth_helpers import *
from google.appengine.ext import ndb
from google.appengine.api import users
from google.appengine.ext.webapp import blobstore_handlers
from random import randint
import unicodedata
from time import sleep
import csv
import StringIO
import json


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

    def get(self, deployment_slug=None):
        user = self.user
        dep = None
        if deployment_slug:
            dep = Deployment.query(Deployment.slug == deployment_slug).fetch(1)
            if dep and len(dep) > 0:
                dep = dep[0]
            else:
                dep = None

        if (user):
            if dep:
                params = self.get_params_hash(
                    userprofile=user.profile, logo_url=dep.logo_url)
            else:
                params = self.get_params_hash(userprofile=user.profile)
            self.render_template('index.html', params)
        else:
            if dep:
                params = self.get_params_hash(logo_url=dep.logo_url)
            else:
                params = {}
            self.render_template('index.html', params)


class UploadHandler(blobstore_handlers.BlobstoreUploadHandler):

    def post(self):
        try:
            upload = self.get_uploads()[0]
            self.response.headers['Content-Type'] = 'application/json'
            obj = {'success': 'true', 'key': str(upload.key()), }
            self.response.out.write(json.dumps(obj))
        except:
            self.error(500)


class DeploymentHandler(BaseHandler):

    @deployment_admin_required
    def post(self, deployment_slug):
        name = self.request.get('name')
        new_slug = self.request.get('slug')
        custom_dns = self.request.get('custom_dns')
        custom_subdomain = self.request.get('custom_subdomain')
        logo_url = self.request.get('logo_url')

        existing_deployment = Deployment.query(
            Deployment.slug == deployment_slug).fetch(1)
        if not existing_deployment or len(existing_deployment) < 1:
            params = {'error': "true",
                      'flash_message': "Error - doesn't exist!"}
            self.render_template('deployments_index.html', params)
            return

        existing_deployment = existing_deployment[0]
        tmp_deployment_slug = None
        tmp_deployment_custom_dns = None
        tmp_deployment_subdomain = None

        if not (new_slug == deployment_slug):
            tmp_deployment_slug = Deployment.query(
                Deployment.slug == new_slug).fetch(1)

        if not (custom_dns == existing_deployment.custom_dns):
            tmp_deployment_custom_dns = Deployment.query(Deployment.custom_dns == custom_dns,
                                                         Deployment.custom_subdomain == custom_subdomain).fetch(1)

        if ((tmp_deployment_slug and len(tmp_deployment_slug)) or
                (tmp_deployment_custom_dns and len(tmp_deployment_custom_dns))):
            deployments = self.user.get_deployments()
            params = {'error': "true", 'flash_message': "Error - already exists!",
                      'deployments': deployments}
            self.render_template('deployments_index.html', params)
        else:
            existing_deployment.name = name
            existing_deployment.slug = new_slug
            existing_deployment.custom_dns = custom_dns
            existing_deployment.custom_subdomain = custom_subdomain
            existing_deployment.put()

            if existing_deployment.logo_url != logo_url:
                existing_deployment.upload_img(logo_url)

            sleep(0.5)
            deployments = self.user.get_deployments()
            params = {'success': "true", 'flash_message': "Successfully update Deployment:  " +
                      existing_deployment.name, 'deployments': deployments}
            self.render_template('deployments_index.html', params)


class StudentHandler(BaseHandler):

    def handlerequest(self, deployment_slug):
        visitor_id = self.request.get('visitor_id', '').strip()

        if (visitor_id == '' or not deployment_slug):
            self.render_template('error_page.html')
        else:
            deployment = Deployment.query(
                Deployment.slug == deployment_slug).get()
            if not deployment:
                self.render_template('error_page.html')

            qry = Visitor.query(Visitor.visitor_id == visitor_id,
                                Visitor.deployment_key == deployment.key)
            visitor = qry.get()

            if (visitor):
                vkey = visitor.key
                maps = MapUserToVisitor.query(
                    MapUserToVisitor.visitor_key == vkey).fetch()
                profiles = []
                for map_item in maps:
                    ukey = map_item.user_key
                    u = User.get_by_id(ukey.id(), parent=ukey.parent(
                    ), app=ukey.app(), namespace=ukey.namespace())
                    if ("<h1>Edit your profile" in u.profile and ">here</a></h1>" in u.profile and len(u.profile) < 60):
                        profiles.append("<h2>" + u.vendorname + "</h2>" +
                                        "<h3>This organization hasn't included any information)</h3>")
                    else:
                        profiles.append(
                            "<h2>" + u.vendorname + "</h2>" + u.profile)

                params = {'profiles': profiles}
                self.render_template('student.html', params)
            else:
                params = {'error': "true",
                          'flash_message': "No such student " + visitor_id}
                self.render_template('studentlogin.html', params)

    def get(self):
        visitor_id = self.request.get('visitor_id', '')
        if (visitor_id == ''):
            self.render_template('studentlogin.html')
        else:
            self.handlerequest()

    def post(self):
        self.handlerequest()


class SignInHandler(BaseHandler):

    def handlerequest(self, deployment_slug=None):
        raw_password = self.request.get('password')
        login = self.request.get('username')
        redirect_to = self.request.get('redirect_to', '')
        tmp_user = User.get_by_username(login)

        if tmp_user:
            user_id = tmp_user.get_id()
            if security.check_password_hash(raw_password, tmp_user.password):
                self.auth.set_session(self.auth.store.user_to_dict(tmp_user))

                if (redirect_to != ''):
                    self.redirect(unicodedata.normalize(
                        'NFKD', redirect_to).encode('ascii', 'ignore'), abort=False)
                else:
                    if deployment_slug:
                        self.redirect(self.uri_for(
                            'deployment_home', deployment_slug=deployment_slug), abort=False)
                    else:
                        self.redirect(self.uri_for('home'), abort=False)
            else:
                params = {'error': "true",
                          'flash_message': "Error signing in - please try again"}
                self.render_template('sign_in.html', params)

        else:
            params = {'error': "true",
                      'flash_message': "Error signing in - please try again"}
            self.render_template('sign_in.html', params)

    def get(self, deployment_slug=None):
        raw_password = self.request.get('password', '')
        login = self.request.get('username', '')
        redirect_to = self.request.get('redirect_to', '')

        if (raw_password != '' and login != ''):
            self.handlerequest(deployment_slug)
        else:
            if deployment_slug:
                dep = Deployment.query(
                    Deployment.slug == deployment_slug).fetch(1)
                if dep and len(dep) > 0:
                    params = self.get_params_hash(
                        redirect_to=redirect_to, logo_url=dep[0].logo_url)
            else:
                params = self.get_params_hash(redirect_to=redirect_to)

            self.render_template('sign_in.html', params)

    def post(self, deployment_slug=None):
        self.handlerequest(deployment_slug)


class SignOutHandler(BaseHandler):

    def get(self, deployment_slug=None):
        self.auth.unset_session()
        if deployment_slug:
            self.redirect(self.uri_for('deployment_home',
                                       deployment_slug=deployment_slug), abort=False)
        else:
            self.redirect(self.uri_for('home'), abort=False)


class UserEditHandler(BaseHandler):

    def handlerequest(self):
        profile_param = self.request.get('profile', -1)
        if (profile_param == -1):
            user = self.user
            params = {'userprofile': user.profile}
            self.render_template('edit_user.html', params)
        else:
            self.user.profile = profile_param.strip()
            self.user.put()
            tmpuser = self.user
            self.auth.unset_session()
            self.auth.set_session(self.auth.store.user_to_dict(tmpuser))
            self.redirect(self.uri_for('home'), abort=False)


    def get(self):
        self.handlerequest()

    @user_login_required
    def post(self):
        self.handlerequest()


class CheckInHandler(BaseHandler):

    def handlerequest(self, deployment_slug=None):
        visitor_id = self.request.get('visitor_id', -1)
        if (visitor_id == -1):
            self.render_template('checkin_visitor.html')
        else:
            deployment = Deployment.query(
                Deployment.slug == deployment_slug).get()

            if not deployment:
                params = {
                    'error': "true", 'flash_message': "Cannot find deployment " + deployment_slug}
                self.render_template('checkin_visitor.html', params)

            new_map = MapUserToVisitor()
            new_map.user_key = self.user.key
            qry = Visitor.query(Visitor.visitor_id == visitor_id,
                                Visitor.deployment_key == deployment.key)
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
                    self.render_template('successful_checkin.html', params)
                else:
                    params = {
                        'error': "true", 'flash_message': "You've already checked in visitor " + visitor_id}
                    self.render_template('checkin_visitor.html', params)
            else:
                params = {'error': "true",
                          'flash_message': "Cannot find visitor " + visitor_id}
                self.render_template('checkin_visitor.html', params)

    @user_login_required
    def get(self):
        self.handlerequest(None)

    @user_login_required
    def post(self, deployment_slug=None):
        self.handlerequest(deployment_slug)


class UsersHandler(BaseHandler):

    def edit_user(self, old_username, new_username, vendorname, password, is_deployment_admin, email):
        calling_user = self.user
        users = calling_user.get_users()

        edit_user = User.get_by_username(old_username)

        if edit_user:
            if not (new_username.lower() == old_username.lower()):
                tmp_user = User.get_by_username(new_username)

                if tmp_user:
                    params = {'users': users, 'error': "true",
                              'flash_message': "Error - user " + new_username + " already exists."}
                    self.render_template('users_index.html', params)
                    return
                edit_user.username = new_username

            edit_user.vendorname = vendorname

            if not (password == "..."):
                edit_user.set_password(password)

            edit_user.is_deployment_admin = is_deployment_admin in [
                'true', 'True', '1', 'on']
            edit_user.email = email
            edit_user.put()

            params = {'users': users, 'success': "true",
                      'flash_message': "Successfully edited user"}
            self.render_template('users_index.html', params)
            return
        params = {'users': users, 'error': "true",
                  'flash_message': "Could not find user"}
        self.render_template('users_index.html', params)
        return

    def add_user(self, username, vendorname, password, is_deployment_admin, email):
        tmp_user = User.get_by_username(username)

        if tmp_user:
            return "Error - user " + username + " already exists."
        else:
            if not username:
                return "Error - username cannot be blank."

            newuser = User()
            newuser.username = username
            newuser.vendorname = vendorname
            newuser.set_password(password)
            newuser.is_deployment_admin = is_deployment_admin in [
                'true', 'True', '1', 'on']
            newuser.profile = '<h1>Edit your profile <a href = "/edit">here</a></h1>'
            newuser.email = email
            newuser.put()
            sleep(0.5)
            return ""

    @deployment_admin_required
    def get(self):
        editing_username = self.request.get('editing_username', '')
        users = self.user.get_users()
        deployments = self.user.get_deployments()
        params = {'users': users, 'deployments': deployments,
                  'editing_username': editing_username}
        self.render_template('users_index.html', params)

    @deployment_admin_required
    def post(self):
        calling_user = self.user

        username = self.request.get('username')
        vendorname = self.request.get('vendorname')
        password = self.request.get('password')
        is_deployment_admin = self.request.get('is_deployment_admin')
        email = self.request.get('email')

        bulkfile = self.request.get('bulkfile')
        command = self.request.get('command')
        old_username = self.request.get('old_username')

        if bulkfile:
            params = {}
            out_str = ''
            reader = None
            try:
                file_stream = StringIO.StringIO(bulkfile)
                dialect = csv.Sniffer().sniff(file_stream.read(1024))
                file_stream.seek(0)
                has_headers = csv.Sniffer().has_header(file_stream.read(1024))
                file_stream.seek(0)
                reader = csv.reader(file_stream, dialect)
                skipped_header_row = False

                count = 0
                for row in reader:
                    if not skipped_header_row:
                        skipped_header_row = True
                    else:
                        retval = self.add_user(username=row[0], vendorname=row[2], password=row[
                                               3], is_deployment_admin=row[4], email=row[1])
                        count = count + 1
                        if retval is not "":
                            users = calling_user.get_users()
                            params = {'users': users, 'error': "true",
                                      'flash_message': retval}
                            self.render_template('users_index.html', params)
                            return
                users = calling_user.get_users()
                params = {'users': users, 'success': "true",
                          'flash_message': "Successfully added " + str(count) + " users."}
                self.render_template('users_index.html', params)
                return
            except csv.Error as e:
                if reader:
                    params = {'users': users, 'error': "true",
                              'flash_message': "File Error - line %d: %s" % (reader.line_num, e)}
                else:
                    params = {'users': users, 'error': "true",
                              'flash_message': "Please verify file format - standard CSV with a header row."}

                self.render_template('users_index.html', params)
                return
            except:
                users = calling_user.get_users()
                params = {'users': users, 'error': "true",
                          'flash_message': "Unknown file error - please use a standard CSV with a header row."}
                self.render_template('users_index.html', params)
                return
        elif command.lower() == "edit":
            return self.edit_user(old_username, username, vendorname, password, is_deployment_admin, email)
        else:
            retval = self.add_user(username=username, vendorname=vendorname,
                                   password=password, is_deployment_admin=is_deployment_admin, email=email)
            users = calling_user.get_users()

            if retval is not "":
                params = {'users': users, 'error': "true",
                          'flash_message': retval}
            else:
                params = {'users': users, 'Success': "true",
                          'flash_message': "Successfully created User:  " + username}

            self.render_template('users_index.html', params)


class VisitorsHandler(BaseHandler):

    def handlerequest(self):
        visitor_id = self.request.get('visitor_id')

        qry = Visitor.query(Visitor.visitor_id == visitor_id)
        visitor = qry.get()
        if (visitor is None):
            newvisitor = Visitor()
            newvisitor.visitor_id = visitor_id
            newvisitor.put()
            params = {'success': "true",
                      'flash_message': "Successfully created Visitor:  " + newvisitor.visitor_id}
            self.render_template('visitors_index.html', params)
        else:
            params = {'error': "true", 'flash_message': "Error - visitor " +
                      visitor_id + " already exists!"}
            self.render_template('visitors_index.html', params)

    @deployment_admin_required
    def get(self):
        visitor_id = self.request.get('visitor_id', -1)
        if (visitor_id == -1):
            self.render_template('visitors_index.html')
        else:
            self.handlerequest()

    @deployment_admin_required
    def post(self):
        self.handlerequest()


class RandomVisitorHandler(BaseHandler):

    @deployment_admin_required
    def get(self):
        # get count
        entity_count = MapUserToVisitor.query().count()

        # get random number
        random_index = randint(0, entity_count - 1)

        # Get all the keys, not the Entities
        maps = MapUserToVisitor.query().order(MapUserToVisitor.key).fetch()

        counter = 0
        for map_item in maps:
            if (random_index == counter):
                key = map_item.visitor_key
                rand_visitor = Visitor.get_by_id(
                    key.id(), parent=key.parent(), app=key.app(), namespace=key.namespace())
                params = {'visitor_id': rand_visitor.visitor_id}
                self.render_template('raffle_results.html', params)
                return
            counter = counter + 1


class DeploymentsHandler(BaseHandler):

    @deployment_admin_required
    def get(self):
        editing_slug = self.request.get('editing_slug', '')
        deployments = Deployment.query()
        params = {'deployments': deployments, 'editing_slug': editing_slug}
        self.render_template('deployments_index.html', params)

    @super_admin_required
    def post(self):
        name = self.request.get('name')
        slug = self.request.get('slug')
        custom_dns = self.request.get('custom_dns')
        custom_subdomain = self.request.get('custom_subdomain')
        logo_url = self.request.get('logo_url', '')

        tmp_deployment_slug = Deployment.query(
            Deployment.slug == slug).fetch(1)
        tmp_deployment_custom_dns = Deployment.query(Deployment.custom_dns == custom_dns,
                                                     Deployment.custom_subdomain == custom_subdomain).fetch(1)

        if ((tmp_deployment_slug and len(tmp_deployment_slug)) or
                (tmp_deployment_custom_dns and len(tmp_deployment_custom_dns))):
            deployments = Deployment.query()
            params = {'error': "true", 'flash_message': "Error - already exists!",
                      'deployments': deployments}
            self.render_template('deployments_index.html', params)
        else:
            newdeployment = Deployment()
            newdeployment.name = name
            newdeployment.slug = slug
            newdeployment.custom_dns = custom_dns
            newdeployment.custom_subdomain = custom_subdomain
            newdeployment.put()
            if logo_url:
                newdeployment.upload_img(logo_url)
            sleep(0.5)
            deployments = Deployment.query()
            params = {'success': "true", 'flash_message': "Successfully created Deployment:  " +
                      newdeployment.name, 'deployments': deployments}
            self.render_template('deployments_index.html', params)


class MapUserToVisitorHandler(BaseHandler):

    @deployment_admin_required
    def get(self):
        self.response.out.write("MapUserToVisitorHandler get")


config = {
    'webapp2_extras.auth': {
        'user_model': 'auth_helpers.User',
        'user_attributes': ['username', 'email', 'is_super_admin', 'is_deployment_admin', 'sudoer']
    },
    'webapp2_extras.sessions': {
        'secret_key': 'YOUR_SECRET_KEY'
    }
}

app = webapp2.WSGIApplication([
    webapp2.Route('/', MainPage, name='home'),

    webapp2.Route('/deployments/view/<deployment_slug>/',
                  MainPage, name='deployment_home'),

    webapp2.Route('/sign_in', SignInHandler, name='sign_in'),
    webapp2.Route('/deployments/view/<deployment_slug>/sign_in',
                  SignInHandler, name='sign_in_deployments'),

    webapp2.Route('/sign_out', SignOutHandler, name='sign_out'),
    webapp2.Route('/deployments/view/<deployment_slug>/sign_out',
                  SignOutHandler, name='sign_out_deployments'),

    webapp2.Route('/checkin_visitor', CheckInHandler, name='checkin'),
    ##webapp2.Route('/deployments/view/<deployment_slug>/checkin_visitor',
##                  CheckInHandler, name='checkin_deployments'),

    webapp2.Route('/deployments/<deployment_slug>/',
                  DeploymentHandler, name='deployment_main'),

    webapp2.Route('/edit', UserEditHandler, name='edit'),

    webapp2.Route('/upload_image', UploadHandler, name='upload'),
    webapp2.Route('/error', ErrorPage, name='error'),

    webapp2.Route('/deployments', DeploymentsHandler, name='deployments'),
    webapp2.Route('/users', UsersHandler, name='users'),
    webapp2.Route('/visitors', VisitorsHandler, name='visitors'),

    webapp2.Route('/<deployment_slug>/student',
                  StudentHandler, name='student'),
    webapp2.Route('/<deployment_slug>/admin_panel/get_random_visitor',
                  RandomVisitorHandler, name='random_visitor'),
    webapp2.Route('/<deployment_slug>/admin_panel/get_all_map_user_to_visitors',
                  MapUserToVisitorHandler, name='list_maps')

], config=config, debug=True)
