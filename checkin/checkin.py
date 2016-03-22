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

        greetings = ndb.gql('SELECT * '
                            'FROM Greeting '
                            'WHERE ANCESTOR IS :1 '
                            'ORDER BY date DESC LIMIT 10',
                            guestbook_key)

        for greeting in greetings:
            if greeting.author:
                self.response.out.write('<b>%s</b> wrote:' %
                                        greeting.author.nickname())
            else:
                self.response.out.write('An anonymous person wrote:')
            self.response.out.write('<blockquote>%s</blockquote>' %
                                    cgi.escape(greeting.content))

        self.response.out.write("""
          <form action="/sign" method="post">
            <div><textarea name="content" rows="3" cols="60"></textarea></div>
            <div><input type="submit" value="Sign Guestbook"></div>
          </form>
        </body>
      </html>""")


class SignInHandler(BaseHandler):

    def get(self):
        self.render_template('sign_in.html')

    def post(self):
        self.render_template('success_page.html')


class SignOutHandler(BaseHandler):

    def get(self):
        self.render_template('success_page.html')

    def post(self):
        self.render_template('success_page.html')


class CheckInHandler(BaseHandler):

    def get(self):
        greeting = Greeting(parent=guestbook_key)

        if users.get_current_user():
            greeting.author = users.get_current_user()

            greeting.content = self.request.get('content')
            greeting.put()

        self.render_template('checkin_visitor.html')

    def post(self):
        self.render_template('success_page.html')


class UserHandler(BaseHandler):

    def get(self):
        self.render_template('add_user.html')

    def post(self):
        name = self.request.get('name')
        password = self.request.get('password')
        is_admin = self.request.get('admin')
        unique_properties = ['name']
        user_data = self.user_model.create_user(user_name, unique_properties,
                                                name=name, password_raw=password, verified=True)
        if not user_data[0]:  # user_data is a tuple
            self.display_message('Unable to create user for email %s because of \
        duplicate keys %s' % (user_name, user_data[1]))
            return
        user = user_data[1]
        user_id = user.get_id()

        token = self.user_model.create_signup_token(user_id)

        self.render_template('success_page.html')


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


class Guestbook(BaseHandler):

    def handle_request(self):
        greeting = Greeting(parent=guestbook_key)

        if users.get_current_user():
            greeting.author = users.get_current_user()

        greeting.content = self.request.get('content')
        greeting.put()
        self.redirect('/')

    def get(self):
        self.handle_request()

    def post(self):
        self.handle_request()


config = {
    'webapp2_extras.auth': {
        'user_model': 'user',
        'user_attributes': ['name']
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
    ('/admin/users', UserHandler),
    ('/admin/visitors', VisitorHandler),
    ('/admin/get_random_visitor', RandomVisitorHandler),
    ('/admin/get_all_map_user_to_visitors', MapUserToVisitorHandler),
], config=config, debug=True)
