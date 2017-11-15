from services.user_service import *
from models.map_user_to_deployment import *

class MapUserToDeploymentService:
    @staticmethod
    def get_users(deployment):
        qry2 = MapUserToDeployment.query(MapUserToDeployment.deployment_key == deployment.key)
        map_users_keys = qry2.fetch(projection=[MapUserToDeployment.user_key],limit=1000)
        users = []
        for mp in map_users_keys:
            u = mp.user_key.get()
            users.append(u)
        return users

    @staticmethod
    def get_users_by_user_deployment(user,deployment=None):
        if user.is_super_admin and user.is_super_admin == True:
            if deployment:
                qry2 = MapUserToDeployment.query(MapUserToDeployment.deployment_key == deployment.key)
                map_users_keys = qry2.fetch(projection=[MapUserToDeployment.user_key])
                users = ndb.get_multi(map_users_keys).order(User.vendorname)
                return users
            else:
                return User.query().order(User.vendorname)
        elif user.is_deployment_admin and user.is_deployment_admin == True:
            qry = MapUserToDeployment.query(MapUserToDeployment.user_key == user.key)
            map_deps = qry.fetch(projection=[MapUserToDeployment.deployment_key])
            if deployment:
                if deployment.key in map_deps:
                    map_deps = [deployment.key]
                else:
                    return []
            qry2 = MapUserToDeployment.query(MapUserToDeployment.deployment_key.IN(map_deps))
            map_users_keys = qry2.fetch(projection=[MapUserToDeployment.user_key])
            users = ndb.get_multi(map_users_keys).order(User.vendorname)
            return users
        else:
            return []

    @staticmethod
    def get_deployments(user):
        if user.is_super_admin and user.is_super_admin == True:
            return Deployment.query().fetch()
        elif user.is_deployment_admin and user.is_deployment_admin == True:
            qry = MapUserToDeployment.query(MapUserToDeployment.user_key == user.key)
            map_deps_keys = qry.fetch(projection=[MapUserToDeployment.deployment_key])
            deployments = ndb.get_multi(map_deps_keys)
            return deployments
        else:
            return []

    @staticmethod
    def add_users_in_bulk(deployment,bulkfile):
        params = {}
        out_str = ''
        reader = None
        try:
            reader = deployment.get_csv_reader(bulkfile)

            count = 0
            skipped_header_row = False
            for row in reader:
                if not skipped_header_row:
                    skipped_header_row = True
                else:
                    retval = MapUserToDeploymentService.add_user(deployment,username=row[0], vendorname=row[2], password=row[3], is_deployment_admin=row[4], email=row[1])
                    count = count + 1
                    if retval is not "":
                        return retval
            return ""
        except csv.Error as e:
            if reader:
                return "File Error - line %d: %s" % (reader.line_num, e)
            else:
                return "Please verify file format - standard CSV with a header row. " + str(e)

        except Exception as e:
            return "Unknown file error - please use a standard CSV with a header row. "  + str(e)

    @staticmethod
    def add_user(deployment, username, vendorname, password, is_deployment_admin, email):
        tmp_user = UserService.get_by_username(username,deployment_key = deployment.key)

        if tmp_user:
            return "Error - user " + username + " already exists."
        else:
            if not username:
                return "Error - username cannot be blank."

            newuser = User()
            newuser.username = username
            newuser.vendorname = vendorname
            newuser.set_password(password)
            newuser.is_deployment_admin = is_deployment_admin in ['true', 'True', '1', 'on']
            newuser.deployment_key = deployment.key
            newuser.profile = '<h1>Edit your profile <a href = "edit">here</a></h1>'
            newuser.email = email
            newuser.put()
            sleep(0.5)

            new_map = MapUserToDeployment()
            new_map.user_key = newuser.key
            new_map.deployment_key = deployment.key
            new_map.put()
            sleep(0.5)
            return ""

    @staticmethod
    def edit_user(deployment, old_username, new_username, vendorname, password, is_deployment_admin, email):
        edit_user = UserService.get_by_username(old_username,deployment_key=deployment.key)

        if edit_user:
            if not (new_username.lower() == old_username.lower()):
                tmp_user = UserService.get_by_username(new_username,deployment_key=deployment.key)

                if tmp_user:
                    return "Error - user " + new_username + " already exists."

                edit_user.username = new_username

            edit_user.vendorname = vendorname

            if (password != edit_user.password):
                edit_user.set_password(password)

            edit_user.is_deployment_admin = is_deployment_admin in [
                'true', 'True', '1', 'on']
            edit_user.email = email
            edit_user.put()

            maps = MapUserToDeployment.query(MapUserToDeployment.user_key == edit_user.key)
            for map in maps:
                map.key.delete()

            new_map = MapUserToDeployment()
            new_map.user_key = edit_user.key
            new_map.deployment_key = deployment.key
            new_map.put()
            sleep(0.5)
            return ""
        return "Could not find user"

    @staticmethod
    def delete_user(deployment,username):
        delete_user = UserService.get_by_username(username,deployment_key=deployment.key)

        maps = MapUserToDeployment.query(MapUserToDeployment.user_key == delete_user.key)
        for map in maps:
            map.key.delete()

        delete_user.key.delete()
        sleep(0.5)
        return ""
