# Checkin
Checkin is the source code that powers http://check-me-in.biz/
It is a convention, career-fair checkin app developed by John Langhauser and Nathaniel Granor for work with <a href="https://www.tealsk12.org/">TEALS</a>

# Notes
dev_appserver.py . --enable_console
tough-variety-126419
appcfg.py --no_cookies -A tough-variety-126419 -V v1 update checkin/
appcfg.py -A tough-variety-126419 -V v9 update checkin/
appcfg.py -A tough-variety-126419 -V v10 update checkin/
appcfg.py -A tough-variety-126419 -V v12 update checkin/

gcloud app deploy --project tough-variety-126419 --version v14 checkin/app.yaml
gcloud app deploy --project tough-variety-126419 checkin/index.yaml


admin?method=GENERATE_QR_CODES&start_at_one=true&qr_codes_to_generate=2000
pip install -t lib -r requirements.txt

pip install -t lib datatables
pip install -t lib requests

# install
source env/bin/activate
pip install --ignore-installed --target=lib pyqrnative
pip install --ignore-installed --target=lib virtualenv
pip install --ignore-installed --target=lib qrcode
pip install --ignore-installed --target=lib pillow
pip install --ignore-installed --target=lib pyqrcode
pip install --ignore-installed --target=lib pypng

pip install git+git://github.com/ojii/pymaging.git#egg=pymaging --target=lib
pip install git+git://github.com/ojii/pymaging-png.git#egg=pymaging-png --target=lib

https://github.com/bernii/PyQRNativeGAE/


pip install pyqrnative


# Bootstrapping users
from models.user import User
user = User(is_super_admin=True, username='John')
user.set_password('tester')
user.put()

from models.raffle_entry import *
entries = RaffleEntry.query().fetch()
for entry in entries:
   entry.key.delete()

from models.map_user_to_visitor import *
entries = MapUserToVisitor.query().fetch()
for entry in entries:
  entry.key.delete()

from models.visitor import *
entries = Visitor.query().fetch()
for entry in entries:
  entry.key.delete()  
