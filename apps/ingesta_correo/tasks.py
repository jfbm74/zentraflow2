# apps/ingesta_correo/tasks.py
from apps.configuracion.services.oauth_verification_service import OAuthVerificationService
from apps.tenants.models import Tenant

def sync_oauth_and_service_status():
    """Tarea programada para sincronizar el estado de OAuth y el servicio de ingesta."""
    for tenant in Tenant.objects.filter(is_active=True):
        # Verificar y actualizar el estado
        OAuthVerificationService.verify_connection(tenant)