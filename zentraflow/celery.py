from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Configurar variables de entorno para Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zentraflow.settings')

app = Celery('zentraflow')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """Configura tareas periódicas de Celery."""
    
    # Tarea de inicialización que se ejecuta una vez al inicio
    sender.add_task(
        'apps.ingesta_correo.tasks.init_ingesta_services',
        queue='ingesta',
        routing_key='ingesta.init'
    )
    
    # Verificación de servicios programados (cada minuto)
    sender.add_periodic_task(
        60.0,
        'apps.ingesta_correo.tasks.check_scheduled_services',
        name='verificar_servicios_programados',
        queue='ingesta',
        routing_key='ingesta.check'
    )
    
    # Sincronización de estado OAuth cada hora
    sender.add_periodic_task(
        3600.0,
        'apps.ingesta_correo.tasks.sync_oauth_and_service_status',
        name='sincronizar_oauth_estado',
        queue='ingesta',
        routing_key='ingesta.sync'
    )

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')