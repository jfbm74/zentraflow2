from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Configurar variables de entorno para Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zentraflow.settings')

app = Celery('zentraflow')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()