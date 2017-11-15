#!/usr/bin/env python
import cgi
import datetime
import webapp2
from array import *
from base.auth_helpers import *
from google.appengine.ext import ndb
from google.appengine.api import users
from google.appengine.ext.webapp import blobstore_handlers
from random import randint
import unicodedata
from time import sleep
import csv
import StringIO
import json
from services.user_service import *
from services.deployment_service import *
from reports import *
from sample import *
from pages import *
from services.map_user_to_deployment_service import *

class UsersHandler(BaseHandler):

    def get_deployment_params(self,deployment):
        params = {}
        params['logo_url'] = deployment.logo_url
        params['header_color'] = deployment.header_background_color
        params['footer_text'] =  deployment.footer_text
        return params

    def edit_user(self, old_username, new_username, vendorname, password, is_deployment_admin, email,deployment_slug):
        calling_user = self.user
        users = MapUserToDeploymentService.get_users_by_user_deployment(calling_user)

        edit_user = UserService.get_by_username(old_username)

        if edit_user:
            if not (new_username.lower() == old_username.lower()):
                tmp_user = UserService.get_by_username(new_username)

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

            dep = Deployment.get_by_slug(deployment_slug)
            if not dep:
                params = {'users': users, 'error': "true",
                              'flash_message': "Invalid Deployment_slug: " + deployment_slug}
                self.render_template('users_index.html', params)
                return

            maps = MapUserToDeployment.query(MapUserToDeployment.user_key == edit_user.key)
            for map in maps:
                map.key.delete()

            new_map = MapUserToDeployment()
            new_map.user_key = edit_user.key
            new_map.deployment_key = dep.key
            new_map.put()

            params = {'users': users, 'success': "true",
                      'flash_message': "Successfully edited user"}
            self.render_template('users_index.html', params)
            return
        params = {'users': users, 'error': "true",
                  'flash_message': "Could not find user"}
        self.render_template('users_index.html', params)
        return

    def add_user(self, username, vendorname, password, is_deployment_admin, email,deployment_slug):
        tmp_user = UserService.get_by_username(username)

        if tmp_user:
            return "Error - user " + username + " already exists."
        else:
            if not username:
                return "Error - username cannot be blank."

            dep = Deployment.get_by_slug(deployment_slug)
            if not dep:
                return "Invalid deployment_slug: " + deployment_slug

            newuser = User()
            newuser.username = username
            newuser.vendorname = vendorname
            newuser.set_password(password)
            newuser.is_deployment_admin = is_deployment_admin in ['true', 'True', '1', 'on']
            newuser.profile = '<h1>Edit your profile <a href = "edit">here</a></h1>'
            newuser.email = email
            newuser.put()
            sleep(0.5)

            new_map = MapUserToDeployment()
            new_map.user_key = newuser.key
            new_map.deployment_key = dep.key
            new_map.put()
            return ""

    @deployment_admin_required
    def get(self):
        editing_username = self.request.get('editing_username', '')
        deployments = MapUserToDeploymentService.get_deployments(self.user)
        params = {'deployments': deployments,
                   'deployment_len': len(deployments),
                  'editing_username': editing_username}

        if len(deployments) > 0:
            params["selected_deployment_slug"] = deployments[0].slug
            params['users'] = MapUserToDeploymentService.get_users_by_user_deployment(self.user, deployments[0])
        else:
            params["selected_deployment_slug"] = ""
            params['users'] = MapUserToDeploymentService.get_users_by_user_deployment(self.user)

        self.render_template('users_index.html', params)

    @deployment_admin_required
    def post(self):
        calling_user = self.user

        selected_deployment_slug = self.request.get('selected_deployment_slug')
        deployment_slug = self.request.get('deployment_slug')
        username = self.request.get('username')
        vendorname = self.request.get('vendorname')
        password = self.request.get('password')
        is_deployment_admin = self.request.get('is_deployment_admin')
        email = self.request.get('email')

        bulkfile = self.request.get('bulkfile')
        command = self.request.get('command')
        old_username = self.request.get('old_username')

        if selected_deployment_slug:
            editing_username = self.request.get('editing_username', '')
            users = MapUserToDeploymentService.get_users_by_user_deployment(self.user)
            deployments = MapUserToDeploymentService.get_deployments(self.user)
            params = {'users': users, 'deployments': deployments,
                      'editing_username': editing_username,
                      'selected_deployment_slug' : selected_deployment_slug}
            self.render_template('users_index.html', params)
            return

        if bulkfile:
            params = {}
            out_str = ''
            reader = None
            try:
                reader = self.get_csv_reader(bulkfile)

                count = 0
                skipped_header_row = False
                for row in reader:
                    if not skipped_header_row:
                        skipped_header_row = True
                    else:
                        retval = self.add_user(username=row[0], vendorname=row[2], password=row[
                                               3], is_deployment_admin=row[4], email=row[1],deployment_slug=row[5])
                        count = count + 1
                        if retval is not "":
                            users = MapUserToDeploymentService.get_users_by_user_deployment(calling_user)
                            params = {'users': users, 'error': "true",
                                      'flash_message': retval}
                            self.render_template('users_index.html', params)
                            return
                users = MapUserToDeploymentService.get_users_by_user_deployment(calling_user)
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
                users = MapUserToDeploymentService.get_users_by_user_deployment(calling_user)
                params = {'users': users, 'error': "true",
                          'flash_message': "Unknown file error - please use a standard CSV with a header row."}
                self.render_template('users_index.html', params)
                return
        elif command.lower() == "edit":
            return self.edit_user(old_username, username, vendorname, password, is_deployment_admin, email,deployment_slug)
        else:
            retval = self.add_user(username=username, vendorname=vendorname,
                                   password=password, is_deployment_admin=is_deployment_admin, email=email,
                                   deployment_slug=deployment_slug)
            users = MapUserToDeploymentService.get_users_by_user_deployment(calling_user)

            if retval is not "":
                params = {'users': users, 'error': "true",
                          'flash_message': retval}
            else:
                params = {'users': users, 'Success': "true",
                          'flash_message': "Successfully created User:  " + username}

            self.render_template('users_index.html', params)

class SignInHandler(BaseHandler):
    def get_deployment_params(self,deployment):
        params = {}
        params['logo_url'] = deployment.logo_url
        params['header_color'] = deployment.header_background_color
        params['footer_text'] =  deployment.footer_text
        return params

    def handlerequest(self, deployment_slug=None):
        raw_password = self.request.get('password')
        login = self.request.get('username')
        redirect_to = self.request.get('redirect_to', '')
        deployment = None
        tmp_user = None

        if deployment_slug:
            deployment = Deployment.get_by_slug(deployment_slug)
            tmp_user = UserService.get_by_username(login,deployment_key=deployment.key)
        else:
            tmp_user = UserService.get_by_username(login)

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
                dep = None
                params = {}
                if deployment_slug:
                    dep = Deployment.get_by_slug(deployment_slug)

                if dep:
                    params = self.get_deployment_params(dep)

                params['error'] = "true"
                params['flash_message'] = "Error signing in - please try again"
                self.render_template('sign_in.html', params)

        else:
            dep = None
            params = {}
            if deployment_slug:
                dep = Deployment.get_by_slug(deployment_slug)

            if dep:
                params = self.get_deployment_params(dep)

            params['error'] = "true"
            params['flash_message'] = "Error signing in - please try again"

            self.render_template('sign_in.html', params)

    def get(self, deployment_slug=None):
        params = {}
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
                    dep = dep[0]
                    params = self.get_params_hash(self.get_deployment_params(dep),
                        redirect_to=redirect_to)
            else:
                params = self.get_params_hash({},redirect_to=redirect_to)

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
    def get_deployment_params(self,deployment):
        params = {}
        params['logo_url'] = deployment.logo_url
        params['header_color'] = deployment.header_background_color
        params['footer_text'] =  deployment.footer_text
        return params

    def handlerequest(self,deployment_slug=None):
        deployment = None
        params = {}
        if deployment_slug:
            deployment = Deployment.get_by_slug(deployment_slug)
            params = self.get_deployment_params(deployment)

        profile_param = self.request.get('profile', -1)
        if (profile_param == -1):
            self.render_template('edit_user.html', self.get_params_hash(params))
        else:
            self.user.profile = profile_param.strip()
            self.user.put()
            tmpuser = self.user
            self.auth.unset_session()
            self.auth.set_session(self.auth.store.user_to_dict(tmpuser))

            if deployment:
                self.redirect(self.request.url.replace("/edit","/"))
            else:
                self.redirect(self.uri_for('home'))


    def get(self,deployment_slug=None):
        self.handlerequest(deployment_slug)

    @user_login_required
    def post(self,deployment_slug=None):
        self.handlerequest(deployment_slug)


class UserRefreshHack(BaseHandler):

    @super_admin_required
    def get(self):
        users = User.query()
        for u in users:
            u.put()
        self.response.out.write("done")
