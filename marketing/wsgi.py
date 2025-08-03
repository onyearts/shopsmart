"""
WSGI config for marketing project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import os
import sys

path = '/home/onyearts/shopsmart'
if path not in sys.path:
    sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'marketing.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
