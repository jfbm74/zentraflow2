from django.apps import AppConfig

class IngestaCorreoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.ingesta_correo'
    verbose_name = 'Ingesta de Correo'

    def ready(self):
        try:
            import apps.ingesta_correo.signals
        except ImportError:
            pass 