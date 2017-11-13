from google.appengine.api import urlfetch
from models.deployment import *
from models.visitor import *
from models.map_user_to_deployment import *
from models.map_user_to_visitor import *
from services.background_job_service import *
from services.child_process_service import *
from services.visitor_service import *

class DeploymentService:

    @staticmethod
    def get_visitors(deployment):
        visitors = Visitor.query(Visitor.deployment_key == self.key).order(Visitor.serialized_id)
        return visitors

    @classmethod
    def create_file(cls,deployment,starting_file=None,starting_offset=0):
        file = starting_file
        zipstream = None

        try:
            zipstream=StringIO.StringIO()
            if file is None:
                file = zipfile.ZipFile(file=zipstream,compression=zipfile.ZIP_DEFLATED,mode="w")

            visitors = Visitor.query(Visitor.deployment_key==deployment.key).order(Visitor.serialized_id).fetch(offset=starting_offset)
            csv = ""
            effective_start = starting_offset
            for v in visitors:
                raw_img = urlfetch.fetch(v.get_qr_code_url()).content
                file.writestr(v.visitor_id + ".png",raw_img)
                effective_start = effective_start +1

            file.close()
            zipstream.seek(0)
            deployment.blocking_task_status = 0
            deployment.put()
            deployment.upload_qr_code_zip(zipstream.getvalue(),'application/zip')

        except DeadlineExceededError:
            deferred.defer(DeploymentService.create_file,deployment,file,effective_start)

    @staticmethod
    def add_bulk_visitors(deployment,bulk_file):
        reader = None
        try:
            reader = deployment.get_csv_reader(bulk_file,False)
            count = 0
            for row in reader:
                retval = deployment.add_visitor(int(row[0]),int(row[1]))
                if retval == 1:
                    return 'Visitor ID already exists'
                elif retval == 2:
                    return 'Serial number already exists'
                elif retval == 3:
                    return 'Visitor already exists'
                elif retval == 4:
                    return 'Visitor cannot have the sample id of 9999999'
                else:
                    count = count + 1
            return ""
        except csv.Error as e:
            if reader:
                return "File Error - line %d: %s" % (reader.line_num, e)
            else:
                return "Please verify file format - standard CSV with a header row."

    @staticmethod
    def get_checkin_raw_data(deployment,csv_writer=None,csv_output=None):
        report = []
        report_csv = "BoothUser,BoothVendor,Student_ID\r"
        users = {}
        visitors = {}

        checkins = MapUserToVisitor.query(MapUserToVisitor.deployment_key == deployment.key)

        if csv_writer:
            csv_writer.writerow(['booth_user', 'booth_vendor','student_id'])

        for checkin in checkins:
            user = None

            if checkin.user_key not in users:
                user = checkin.user_key.get()
                users[checkin.user_key] = user
            else:
                user = users[checkin.user_key]

            report_row_user = user.username if user else 'ERROR'
            report_row_vendor = user.vendorname if user else 'ERROR'

            if checkin.visitor_key not in visitors:
                visitor = Visitor.query(Visitor.key == checkin.visitor_key,
                                    Visitor.deployment_key == deployment.key).fetch(1)
                visitors[checkin.visitor_key] = visitor
            else:
                visitor = visitors[checkin.visitor_key]

            if visitor and len(visitor) > 0 and visitor[0]:
                visitor = visitor[0]
            else:
                visitor = None

            report_row_student_id = visitor.visitor_id if visitor else 'ERROR'

            if csv_writer:
                csv_writer.writerow([report_row['booth_user'],report_row['booth_vendor'],report_row['student_id']])
            if csv_output:
                report_csv = report_csv + str(report_row_user) + "," + str(report_row_vendor)\
                             + "," + str(report_row_student_id) + "\r"
        if csv_output:
            return report_csv
        return report

    @staticmethod
    def get_booth_checkin_report(deployment):
        report = []

        map_list = MapUserToDeployment.query(MapUserToDeployment.deployment_key == deployment.key)
        for map_item in map_list:
            user = User.query(User.key == map_item.user_key).fetch(1)
            if user and len(user) > 0 and user[0] and not user[0].is_super_admin:
                count = MapUserToVisitor.query(MapUserToVisitor.deployment_key == deployment.key,
                                            MapUserToVisitor.user_key == user[0].key).count()
                report.append([user[0].vendorname, count])

        sorted_report_items = sorted(report, key=itemgetter(1))
        sorted_report_items.reverse()
        return sorted_report_items

    @staticmethod
    def get_booth_report(deployment):
        report = []
        edited_count = 0
        unedited_count = 0

        map_list = MapUserToDeployment.query(MapUserToDeployment.deployment_key == deployment.key)
        for map_item in map_list:
            user = User.query(User.key == map_item.user_key).fetch(1)
            if user and len(user) > 0 and user[0] and not user[0].is_super_admin:
                report_row_username = user[0].username
                report_row_email = user[0].email
                report_row_hasedited = None
                if ("<h1>Edit your profile" in user[0].profile
                    and ">here</a></h1>" in user[0].profile
                    and len(user[0].profile) < 60):
                    report_row_hasedited = 'NO'
                    unedited_count = unedited_count + 1
                else:
                    report_row_hasedited = 'YES'
                    edited_count = edited_count + 1
                report.append([report_row_username, report_row_email, report_row_hasedited])
        report_stats = []
        report_stats_row = {}
        report_stats_row['unedited'] = unedited_count
        report_stats_row['edited'] = edited_count
        report_stats.append(report_stats_row)
        return report_stats,report

    @staticmethod
    def set_sample_qr_code(deployment):
        url = deployment.custom_subdomain + "." + deployment.custom_dns + "/checkin_visitor?visitor_id=9999999"
        qr = QRCode(QRCode.get_type_for_string(url), QRErrorCorrectLevel.L)
        qr.addData(url)
        qr.make()
        img = qr.make_image()
        ChildProcessService.upload_qr_code(deployment,img,"image/png")
        sleep(0.5)
