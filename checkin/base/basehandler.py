import cgi
import datetime
import webapp2
from google.appengine.ext import ndb
from google.appengine.api import users
import time
import webapp2_extras.appengine.auth.models
from google.appengine.ext import ndb
from webapp2_extras import security
from webapp2_extras import sessions
from webapp2_extras import auth
import os
import csv
import StringIO
import urllib
from google.appengine.ext.webapp import template

class BaseHandler(webapp2.RequestHandler):
  @webapp2.cached_property
  def auth(self):
    """Shortcut to access the auth instance as a property."""
    return auth.get_auth()

  @webapp2.cached_property
  def user_info(self):
    """Shortcut to access a subset of the user attributes that are stored
    in the session.

    The list of attributes to store in the session is specified in
      config['webapp2_extras.auth']['user_attributes'].
    :returns
      A dictionary with most user information
    """
    return self.auth.get_user_by_session()

  @webapp2.cached_property
  def user(self):
    """Shortcut to access the current logged in user.

    Unlike user_info, it fetches information from the persistence layer and
    returns an instance of the underlying model.

    :returns
      The instance of the user model associated to the logged in user.
    """
    u = self.user_info
    return self.user_model.get_by_id(u['user_id']) if u else None

  @webapp2.cached_property
  def user_model(self):
    """Returns the implementation of the user model.

    It is consistent with config['webapp2_extras.auth']['user_model'], if set.
    """
    return self.auth.store.user_model

  @webapp2.cached_property
  def session(self):
      """Shortcut to access the current session."""
      return self.session_store.get_session(backend="datastore")

  def add_deployment_params(self,starting_array,deployment=None,**kwargs):
    params = starting_array
    if deployment:
        params['deployment'] = deployment
        params['logo_url'] = deployment.logo_url
        params['header_color'] = deployment.header_background_color
        params['footer_text'] =  deployment.footer_text
        params['student_link'] =  deployment.student_link
        params['student_link_text'] =  deployment.student_link_text
        params['user_link'] =  deployment.user_link
        params['user_link_text'] =  deployment.user_link_text
        params['visitors'] =  deployment.get_visitors()
        params['users'] =  deployment.get_users()

    for key, value in kwargs.items():
        params[key] = value

    return params

  def get_params_hash(self,starting_array,**kwargs):
      params = starting_array
      user = self.user
      if user:
        #   sudos = SudoLogin.query(SudoLogin.admin_key == user.key).fetch(1)
        #   if sudos and len(sudos) > 0 and sudos[0]:
        #       user = sudos[0].user_key
        #       params['sudo'] = True
          params['user']= user
          params['userprofile'] = user.profile

      for key, value in kwargs.items():
          params[key] = value
      return params

  def get_csv_reader(self,csv_file,should_sniff=True):
      file_stream = StringIO.StringIO(csv_file)
      if should_sniff:
          dialect = csv.Sniffer().sniff(file_stream.read(1024))
          file_stream.seek(0)
          has_headers = csv.Sniffer().has_header(file_stream.read(1024))
          file_stream.seek(0)
          reader = csv.reader(file_stream, dialect)
      else:
          reader = csv.reader(file_stream)
      return reader

  def render_template(self, view_filename, params={}):
    user = self.user_info
    params['user'] = user
    path = os.path.join(os.path.dirname(__file__), '../views', view_filename)
    self.response.out.write(template.render(path, params))

  def render_smart_template(self, target, source, view_filename, deployment=None, params={}):
    params = self.add_deployment_params(params,deployment)
    if target == 'DEPLOYMENT' and source == 'ADMIN':
        if 'activetab' not in params:
            params['activetab'] = 'domain'
        view_filename = 'admin.html'

    user = self.user_info
    params['user'] = user
    path = os.path.join(os.path.dirname(__file__), '../views', view_filename)
    self.response.out.write(template.render(path, params))

  def display_message(self, message):
    """Utility function to display a template with a simple message."""
    params = {'message': message}
    self.render_template('message.html', params)

  # this is needed for webapp2 sessions to work
  def dispatch(self):
      # Get a session store for this request.
      self.session_store = sessions.get_store(request=self.request)

      try:
          # Dispatch the request.
          webapp2.RequestHandler.dispatch(self)
      finally:
          # Save all sessions.
          self.session_store.save_sessions(self.response)
