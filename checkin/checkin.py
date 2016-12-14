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
from models import *
from reports import *
from sample import *

class ErrorPage(BaseHandler):

    def get(self):
        auth = self.auth
        self.render_template('error_page.html')


class MainPage(BaseHandler):
    def get_deployment_params(self,deployment,**kwargs):
        params = {}
        params['logo_url'] = deployment.logo_url
        params['header_color'] = deployment.header_background_color
        params['footer_text'] =  deployment.footer_text
        params['user_link'] =  deployment.user_link
        params['user_link_text'] =  deployment.user_link_text

        for key, value in kwargs.items():
            params[key] = value
        return params


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
                    self.get_deployment_params(dep,userprofile=user.profile))
            else:
                params = self.get_params_hash({},userprofile=user.profile)
            self.render_template('index.html', params)
        else:
            if dep:
                params = self.get_params_hash(self.get_deployment_params(dep))
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
        header_background_color = self.request.get('header_background_color')
        footer_text = self.request.get('footer_text')
        student_link = self.request.get('student_link')
        student_link_text = self.request.get('student_link_text')
        user_link = self.request.get('user_link')
        user_link_text = self.request.get('user_link_text')

        if len(header_background_color) > 6:
            params = {'error': "true",
                      'flash_message': "Error - background color should be an html color code (6 characters long)"}
            self.render_template('deployments_index.html', params)
            return


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
            existing_deployment.header_background_color = header_background_color
            existing_deployment.footer_text = footer_text
            existing_deployment.student_link = student_link
            existing_deployment.student_link_text = student_link_text
            existing_deployment.user_link = user_link
            existing_deployment.user_link_text = user_link_text
            existing_deployment.put()

            if existing_deployment.logo_url != logo_url:
                existing_deployment.upload_img(logo_url)

            sleep(0.5)
            deployments = self.user.get_deployments()
            params = {'success': "true", 'flash_message': "Successfully update Deployment:  " +
                      existing_deployment.name, 'deployments': deployments}
            self.render_template('deployments_index.html', params)


class StudentHandler(BaseHandler):
    def get_deployment_params(self,deployment):
        params = {}
        params['logo_url'] = deployment.logo_url
        params['header_color'] = deployment.header_background_color
        params['footer_text'] =  deployment.footer_text
        params['student_link'] =  deployment.student_link
        params['student_link_text'] =  deployment.student_link_text
        return params

    def handlerequest(self, deployment_slug=None):
        visitor_id = self.request.get('visitor_id', '').strip()

        if (visitor_id == '' or not deployment_slug):
            self.render_template('error_page.html')
        else:
            deployment = Deployment.get_by_slug(deployment_slug)

            if not deployment:
                self.render_template('error_page.html')

            params = self.get_deployment_params(deployment)

            qry = Visitor.query(Visitor.visitor_id == visitor_id,
                                Visitor.deployment_key == deployment.key)
            visitor = qry.get()

            if (visitor):
                vkey = visitor.key
                maps = MapUserToVisitor.query(
                    MapUserToVisitor.visitor_key == vkey,
                    MapUserToVisitor.deployment_key == deployment.key).fetch()
                profiles = []
                for map_item in maps:
                    ukey = map_item.user_key
                    u = ukey.get()

                    if ( not u.profile
                         or ("<h1>Edit your profile" in u.profile
                         and ">here</a></h1>" in u.profile
                         and len(u.profile) < 60)):
                        profiles.append("<h2>" + u.vendorname + "</h2>" +
                                        "<h3>This organization hasn't included any information)</h3>")
                    else:
                        profiles.append(
                            "<h2>" + u.vendorname + "</h2>" + u.profile)

                params['profiles'] = profiles
                self.render_template('student.html', params)
            else:
                params['error'] = "true"
                params['flash_message'] = "No such student " + visitor_id
                self.render_template('studentlogin.html', params)

    def get(self,deployment_slug=None):
        visitor_id = self.request.get('visitor_id', '')
        if (visitor_id == ''):
            dep = Deployment.get_by_slug(deployment_slug)
            if dep:
                self.render_template('studentlogin.html',self.get_params_hash(self.get_deployment_params(dep)))
            else:
                self.render_template('studentlogin.html')
        else:
            self.handlerequest(deployment_slug)

    def post(self,deployment_slug=None):
        self.handlerequest(deployment_slug)


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


class CheckInHandler(BaseHandler):
    def get_deployment_params(self,deployment):
        params = {}
        params['deployment_slug'] = deployment.slug
        params['logo_url'] = deployment.logo_url
        params['header_color'] = deployment.header_background_color
        params['footer_text'] =  deployment.footer_text
        return params

    def handlerequest(self, deployment_slug=None):
        visitor_id = self.request.get('visitor_id', -1)
        deployment = None
        params = {}
        post_deployment_slug = self.request.get('deployment_slug', None)

        if deployment_slug:
            deployment = Deployment.get_by_slug(deployment_slug)

        if not deployment and post_deployment_slug:
            deployment = Deployment.get_by_slug(post_deployment_slug)

        if deployment:
                params = self.get_deployment_params(deployment)

        if (visitor_id == -1):
            self.render_template('checkin_visitor.html',params)
        else:

            if not deployment:
                params['error'] = "true"
                params['flash_message'] = "Invalid or No Deployment Passed"
                self.render_template('checkin_visitor.html', params)
                return

            new_map = MapUserToVisitor()
            new_map.user_key = self.user.key
            qry = Visitor.query(Visitor.visitor_id == visitor_id,
                                Visitor.deployment_key == deployment.key)
            visitor = qry.get()
            if (visitor or visitor_id == 9999999):
                maps = MapUserToVisitor.query(ndb.AND(
                    MapUserToVisitor.visitor_key == visitor.key,
                    MapUserToVisitor.user_key == self.user.key,
                    MapUserToVisitor.deployment_key == deployment.key)
                ).count(1)

                if (maps == 0):
                    new_map.visitor_key = visitor.key
                    new_map.deployment_key = visitor.deployment_key
                    new_map.put()
                    params['visitor_id'] = visitor_id
                    self.render_template('successful_checkin.html', params)
                else:
                    params['error'] = 'true'
                    params['flash_message'] = "You've already checked in visitor " + visitor_id
                    self.render_template('checkin_visitor.html', params)
            else:
                params['error'] = 'true'
                params['flash_message'] = 'Cannot find visitor ' + visitor_id
                self.render_template('checkin_visitor.html', params)

    @user_login_required
    def get(self, deployment_slug=None):
        self.handlerequest(deployment_slug)

    @user_login_required
    def post(self, deployment_slug=None):
        self.handlerequest(deployment_slug)


class UsersHandler(BaseHandler):

    def get_deployment_params(self,deployment):
        params = {}
        params['logo_url'] = deployment.logo_url
        params['header_color'] = deployment.header_background_color
        params['footer_text'] =  deployment.footer_text
        return params

    def edit_user(self, old_username, new_username, vendorname, password, is_deployment_admin, email,deployment_slug):
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
        tmp_user = User.get_by_username(username)

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
        users = self.user.get_users()
        deployments = self.user.get_deployments()
        params = {'users': users, 'deployments': deployments,
                  'editing_username': editing_username}
        if len(deployments.fetch()) > 0:
            params["selected_deployment_slug"] = deployments.fetch()[0].slug
        else:
            params["selected_deployment_slug"] = ""

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
            users = self.user.get_users()
            deployments = self.user.get_deployments()
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
            return self.edit_user(old_username, username, vendorname, password, is_deployment_admin, email,deployment_slug)
        else:
            retval = self.add_user(username=username, vendorname=vendorname,
                                   password=password, is_deployment_admin=is_deployment_admin, email=email,
                                   deployment_slug=deployment_slug)
            users = calling_user.get_users()

            if retval is not "":
                params = {'users': users, 'error': "true",
                          'flash_message': retval}
            else:
                params = {'users': users, 'Success': "true",
                          'flash_message': "Successfully created User:  " + username}

            self.render_template('users_index.html', params)


class VisitorsHandler(BaseHandler):
    def get_deployment_params(self,deployment):
        params = {}
        params['logo_url'] = deployment.logo_url
        params['header_color'] = deployment.header_background_color
        params['footer_text'] =  deployment.footer_text
        return params

    def add_visitor(self,visitor_id,deployment=None):
        if deployment:
            qry = Visitor.query(Visitor.visitor_id == visitor_id,
                                Visitor.deployment_key == deployment.key)
        else:
            qry = Visitor.query(Visitor.visitor_id == visitor_id)

        visitor = qry.get()
        if (visitor is None and visitor_id != 9999999):
            newvisitor = Visitor()
            newvisitor.visitor_id = visitor_id
            if deployment:
                newvisitor.deployment_key = deployment.key
            newvisitor.put()
            return ""
        else:
            return "Error - Visitor " + visitor_id + " already exists."

    def handlerequest(self,deployment_slug=None,bulk_file=None):
        visitor_id = self.request.get('visitor_id')
        deployment = Deployment.get_by_slug(deployment_slug)

        if bulk_file:
            reader = None
            try:
                reader = self.get_csv_reader(bulk_file,False)
                count = 0
                for row in reader:
                    retval = self.add_visitor(row[0],deployment)
                    if retval is not "":
                        params = {'error': "true",'flash_message': retval}
                        if deployment:
                            params['logo_url'] = deployment.logo_url
                            params['logo_url'] = deployment.logo_url
                            params['header_color'] = deployment.header_background_color
                            params['footer_text'] =  deployment.footer_text

                        self.render_template('visitors_index.html', params)
                        return
                    else:
                        count = count + 1

                if deployment:
                    params = {'success': "true",
                          'flash_message': "Successfully added "
                               + str(count) + " visitors."}

                    params['header_color'] = deployment.header_background_color
                    params['logo_url'] = deployment.logo_url
                    params['footer_text'] =  deployment.footer_text
                else:
                    params = {'success': "true",
                          'flash_message': "Successfully added "
                               + str(count) + " visitors."}

                self.render_template('visitors_index.html', params)
                return
            except csv.Error as e:
                if reader:
                    params = {'users': users, 'error': "true",
                              'flash_message': "File Error - line %d: %s" % (reader.line_num, e)}
                else:
                    params = {'users': users, 'error': "true",
                              'flash_message': "Please verify file format - standard CSV with a header row."}
                self.render_template('visitors_index.html', params)

        else:
            retval = self.add_visitor(visitor_id=visitor_id,
                                      deployment=deployment)
            if retval == "":
                params = {'success': "true",
                          'flash_message': "Successfully created Visitor:  " + newvisitor.visitor_id}
            else:
                params = {'error': "true", 'flash_message': retval}

            if deployment:
                params["logo_url"] = deployment.logo_url
                params['header_color'] = deployment.header_background_color
                params['footer_text'] =  deployment.footer_text

            self.render_template('visitors_index.html', params)

    @deployment_admin_required
    def get(self,deployment_slug=None):
        visitor_id = self.request.get('visitor_id', -1)
        if (visitor_id == -1):
            dep = Deployment.get_by_slug(deployment_slug)

            if dep:
                self.render_template('visitors_index.html',
                            self.get_params_hash(self.get_deployment_params(dep)))
            else:
                self.render_template('visitors_index.html')
        else:
            self.handlerequest()

    @deployment_admin_required
    def post(self,deployment_slug=None):
        bulk_file = self.request.get('bulkfile', None)
        self.handlerequest(deployment_slug,bulk_file)


class RandomVisitorHandler(BaseHandler):
    def get_deployment_params(self,deployment):
        params = {}
        params['logo_url'] = deployment.logo_url
        params['header_color'] = deployment.header_background_color
        params['footer_text'] =  deployment.footer_text
        return params

    @deployment_admin_required
    def get(self,deployment_slug):
        dep = Deployment.get_by_slug(deployment_slug)
        if dep:
            params = self.get_deployment_params(dep)

            # get count
            entity_count = MapUserToVisitor.query(MapUserToVisitor.deployment_key == dep.key).count()

            # get random number
            random_index = randint(0, entity_count - 1)

            # Get all the keys, not the Entities
            maps = MapUserToVisitor.query(MapUserToVisitor.deployment_key == dep.key).order(MapUserToVisitor.key).fetch()

            counter = 0
            for map_item in maps:
                if (random_index == counter):
                    key = map_item.visitor_key
                    rand_visitor = Visitor.get_by_id(
                        key.id(), parent=key.parent(), app=key.app(), namespace=key.namespace())
                    params['visitor_id'] = rand_visitor.visitor_id
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
        header_background_color = self.request.get('header_background_color')
        footer_text = self.request.get('footer_text')
        student_link = self.request.get('student_link')
        student_link_text = self.request.get('student_link_text')
        user_link = self.request.get('user_link')
        user_link_text = self.request.get('user_link_text')

        if len(header_background_color) > 6:
            params = {'error': "true",
                      'flash_message': "Error - background color should be an html color code (6 characters long)"}
            self.render_template('deployments_index.html', params)
            return

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
            newdeployment.header_background_color = header_background_color
            newdeployment.footer_text = footer_text
            newdeployment.student_link = student_link
            newdeployment.student_link_text = student_link_text
            newdeployment.user_link = user_link
            newdeployment.user_link_text = user_link_text

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

class UserRefreshHack(BaseHandler):

    @super_admin_required
    def get(self):
        users = User.query()
        for u in users:
            u.put()
        self.response.out.write("done")

config = {
    'webapp2_extras.auth': {
        'user_model': 'auth_helpers.User',
        'user_attributes': ['username', 'email', 'is_super_admin', 'is_deployment_admin']
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
    webapp2.Route('/deployments/view/<deployment_slug>/checkin_visitor',
                   CheckInHandler, name='checkin_deployments'),

    webapp2.Route('/student',StudentHandler, name='student'),
    webapp2.Route('/deployments/view/<deployment_slug>/student',
                   StudentHandler, name='student_deployments'),

    webapp2.Route('/deployments/<deployment_slug>/',
                  DeploymentHandler, name='deployment_main'),

    webapp2.Route('/deployments/view/<deployment_slug>/visitors',
                  VisitorsHandler, name='visitors_deployments'),

    webapp2.Route('/deployments/view/<deployment_slug>/edit', UserEditHandler, name='edit_deployments'),
    webapp2.Route('/edit', UserEditHandler, name='edit'),

    webapp2.Route('/upload_image', UploadHandler, name='upload'),
    webapp2.Route('/error', ErrorPage, name='error'),

    webapp2.Route('/deployments', DeploymentsHandler, name='deployments'),
    webapp2.Route('/users', UsersHandler, name='users'),

    webapp2.Route('/reports', ReportsHandler, name='reports'),


    webapp2.Route('/deployments/view/<deployment_slug>/sample', SampleHandler, name='sample_deployment'),

    webapp2.Route('/deployments/view/<deployment_slug>/get_random_visitor',
                  RandomVisitorHandler, name='random_visitor'),

    webapp2.Route('/<deployment_slug>/admin_panel/get_all_map_user_to_visitors',
                  MapUserToVisitorHandler, name='list_maps'),


    webapp2.Route('/John/Langhauser/UserRefreshHack',
                  UserRefreshHack, name='hack_refresh')



], config=config, debug=True)
