import os
import sys

# Add your project path to sys.path
path = '/home/shopsmart/shopsmart'
if path not in sys.path:
    sys.path.append(path)

# Set Django settings module
os.environ['DJANGO_SETTINGS_MODULE'] = 'marketing.settings'

# Load WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
