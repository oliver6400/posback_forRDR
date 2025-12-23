import os

from django.core.asgi import get_asgi_application

settings_module = 'core.deployment_render' if 'RENDER_EXTERNAL_HOSTNAME' in os.environ else 'core.settings'
os.environ.setdefault('DJANGO_SETTINGS_MODULE',settings_module )

application = get_asgi_application()
