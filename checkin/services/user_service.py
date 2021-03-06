from models.user import *

class UserService:

    @classmethod
    def get_by_username(cls, username, deployment_key=None, subject='auth'):
        """Returns a user object based on a username.

        :param username:
            The username of the requesting user.

        :returns:
            returns user or none if
        """
        username = username.lower()
        user = None

        if deployment_key:
            user = User.query(User.username == username, User.deployment_key == deployment_key).get()
            if user:
                return user
            qry = User.query(User.username_lower == username, User.deployment_key == deployment_key)
            user = qry.get()
            if user:
                return user

        if user is None:
            qry = User.query(User.username == username,User.is_super_admin == True)
            user = qry.get()

        if user:
            return user

        qry = User.query(User.username_lower == username, User.is_super_admin == True)
        user = qry.get()

        if user:
            return user

        return None
