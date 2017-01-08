# appengine_config.py
from google.appengine.ext import vendor
import sys
sys.path.insert(0, 'lib')

# Add any libraries install in the "lib" folder.
vendor.add('env')
