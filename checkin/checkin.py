from handlers.deployments import *
from handlers.pages import *
from handlers.error_page import *
from handlers.map_user_to_visitors import *
from handlers.reports import *
from handlers.sample import *
from handlers.students import *
from handlers.users import *
from handlers.visitors import *
from handlers.admins import *
from handlers.tasks import *
from handlers.background_jobs import *
from handlers.blob_store import *

config = {
    'webapp2_extras.auth': {
        'user_model': 'base.auth_helpers.User',
        'user_attributes': ['username', 'email', 'is_super_admin', 'is_deployment_admin']
    },
    'webapp2_extras.sessions': {
        'secret_key': 'YOUR_SECRET_KEY'
    }
}

app = webapp2.WSGIApplication([
    webapp2.Route('/', MainPage, name='home'),
    webapp2.Route('/sign_in', SignInHandler, name='sign_in'),
    webapp2.Route('/sign_out', SignOutHandler, name='sign_out'),
    webapp2.Route('/checkin_visitor', CheckInHandler, name='checkin'),
    webapp2.Route('/student',StudentHandler, name='student'),
    webapp2.Route('/edit', UserEditHandler, name='edit'),
    webapp2.Route('/sample', SampleHandler, name='sample_no_deployment'),
    webapp2.Route('/custom-domains',InstructionsHandler, name='domain_instructions'),

    webapp2.Route('/deployments/<deployment_slug>/',DeploymentHandler, name='deployment_main'),
    webapp2.Route('/deployments/view/<deployment_slug>/',MainPage, name='deployment_home'),
    webapp2.Route('/deployments/view/<deployment_slug>/home',MainPage, name='deployment_home_explicit'),
    webapp2.Route('/deployments/view/<deployment_slug>/sign_in',SignInHandler, name='sign_in_deployments'),
    webapp2.Route('/deployments/view/<deployment_slug>/sign_out',SignOutHandler, name='sign_out_deployments'),
    webapp2.Route('/deployments/view/<deployment_slug>/checkin_visitor',CheckInHandler, name='checkin_deployments'),
    webapp2.Route('/deployments/view/<deployment_slug>/student',StudentHandler, name='student_deployments'),
    webapp2.Route('/deployments/view/<deployment_slug>/edit', UserEditHandler, name='edit_deployments'),
    webapp2.Route('/deployments/view/<deployment_slug>/sample', SampleHandler, name='sample_deployment'),
    webapp2.Route('/deployments/view/<deployment_slug>/custom-domains',InstructionsHandler, name='domain_instructions'),

    webapp2.Route('/deployments/view/<deployment_slug>/admin',AdminHandler, name='admin_deployments'),
    webapp2.Route('/deployments/view/<deployment_slug>/backgroundjobs',BackgroundJobs, name='background_jobs'),
    webapp2.Route('/deployments/view/<deployment_slug>/visitorsasync',VisitorsAsyncHandler, name='background_jobs'),
    webapp2.Route('/deployments/view/<deployment_slug>/dump_badges',VisitorDump, name='visitor_export'),
    webapp2.Route('/deployments/view/<deployment_slug>/dump_badges_csv',VisitorCSV, name='visitor_csv'),

    webapp2.Route('/deployments/view/<deployment_slug>/visitors',VisitorsHandler, name='visitors_deployments'),
    webapp2.Route('/deployments/view/<deployment_slug>/get_random_visitor',RandomVisitorHandler, name='random_visitor'),

    webapp2.Route('/blobstore/images/<photo_key>',ViewPhotoHandler, name='blob_server'),

    webapp2.Route('/upload_image', UploadHandler, name='upload'),
    webapp2.Route('/error', ErrorPage, name='error'),
    webapp2.Route('/deployments', DeploymentsHandler, name='deployments'),
    webapp2.Route('/users', UsersHandler, name='users'),
    webapp2.Route('/reports', ReportsHandler, name='reports'),
    webapp2.Route('/John/Langhauser/UserRefreshHack',
                  UserRefreshHack, name='hack_refresh'),

    webapp2.Route('/api/tasks/update_map_user_indices/',
                  TaskHandler, name='cron_tasks')



], config=config, debug=True)
