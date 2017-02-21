# checkin
dev_appserver.py .
tough-variety-126419
appcfg.py --no_cookies -A tough-variety-126419 -V v1 update checkin/
appcfg.py -A tough-variety-126419 -V v9 update checkin/


pip install -t lib -r requirements.txt

pip install -t lib datatables
pip install -t lib requests

# install
source env/bin/activate
pip install --ignore-installed --target=lib qrcode
pip install --ignore-installed --target=lib pillow
pip install --ignore-installed --target=lib pyqrcode
pip install --ignore-installed --target=lib pypng

pip install git+git://github.com/ojii/pymaging.git#egg=pymaging --target=lib
pip install git+git://github.com/ojii/pymaging-png.git#egg=pymaging-png --target=lib
