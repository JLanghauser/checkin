import time
import webapp2_extras.appengine.auth.models

from google.appengine.ext import ndb

from webapp2_extras import security

from urllib import pathname2url


def user_required(handler):
  """
    Decorator that checks if there's a user associated with the current session.
    Will also fail if there's no session present.
  """
  def check_login(self, *args, **kwargs):
    auth = self.auth
    if not auth.get_user_by_session():
     
      self.redirect(self.uri_for('sign_in') + '?params=' + self.request.url, abort=True)
    else:
      return handler(self, *args, **kwargs)

  return check_login

def admin_required(handler):
  """
    Decorator that checks if there's a user associated with the current session.
    And that that user is an admin. Will also fail if there's no session present.
  """
  def check_admin(self, *args, **kwargs):
    auth = self.auth
    if not auth.get_user_by_session():
      self.redirect(self.uri_for('sign_in'), abort=True)
    else:
      if (self.user.is_admin):
        return handler(self, *args, **kwargs)
      else:
        self.redirect(self.uri_for('error'), abort=True)
  return check_admin

class User(webapp2_extras.appengine.auth.models.User):
    is_admin = ndb.BooleanProperty()
    username = ndb.StringProperty()
    profile = ndb.TextProperty()

    def set_password(self, raw_password):
        """Sets the password for the current user

        :param raw_password:
            The raw password which will be hashed and stored
        """
        self.password = security.generate_password_hash(
            raw_password, length=12)

    @classmethod
    def get_by_auth_token(cls, user_id, token, subject='auth'):
        """Returns a user object based on a user ID and token.

        :param user_id:
            The user_id of the requesting user.
        :param token:
            The token string to be verified.
        :returns:
            A tuple ``(User, timestamp)``, with a user object and
            the token timestamp, or ``(None, None)`` if both were not found.
        """
        token_key = cls.token_model.get_key(user_id, subject, token)
        user_key = ndb.Key(cls, user_id)
        # Use get_multi() to save a RPC call.
        valid_token, user = ndb.get_multi([token_key, user_key])
        if valid_token and user:
            timestamp = int(time.mktime(valid_token.created.timetuple()))
            return user, timestamp

        return None, None

    @classmethod
    def get_by_username(cls, username, subject='auth'):
        """Returns a user object based on a username.

        :param username:
            The username of the requesting user.

        :returns:
            returns user or none if
        """
        qry = User.query(User.username == username)
        user = qry.get()

        if user:
            return user
        return None
