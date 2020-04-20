"""
WSGI config for backend project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/howto/deployment/wsgi/
"""

from channels.routing import get_default_application

import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

# Adaptation to run subscriptions (to open websockets) with gunicorn and django
django.setup()
application = get_default_application()
