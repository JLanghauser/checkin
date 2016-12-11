# checkin
dev_appserver.py .
tough-variety-126419
appcfg.py --no_cookies -A tough-variety-126419 -V v1 update checkin/
appcfg.py -A tough-variety-126419 -V v9 update checkin/


# install
source env/bin/activate
pip install --ignore-installed --target=lib qrcode
pip install --ignore-installed --target=lib pillow
pip install --ignore-installed --target=lib pyqrcode
pip install --ignore-installed --target=lib pypng

pip install git+git://github.com/ojii/pymaging.git#egg=pymaging
pip install git+git://github.com/ojii/pymaging-png.git#egg=pymaging-png
