from django.core.management.base import BaseCommand
from apps.ingesta_correo.tasks import sync_oauth_and_service_status

class Command(BaseCommand):
    help = 'Ejecuta manualmente la sincronización de OAuth'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Iniciando sincronización manual de OAuth...'))
        result = sync_oauth_and_service_status()
        self.stdout.write(self.style.SUCCESS(f'Sincronización completada: {result}'))