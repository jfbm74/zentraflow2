import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zentraflow.settings')
django.setup()

from apps.tenants.models import Tenant

def create_default_tenant():
    """Crea un tenant por defecto si no existe."""
    try:
        tenant = Tenant.objects.create(
            name="Default Tenant",
            domain="default.local",
            nit="123456789",
            direccion="Dirección por defecto",
            telefono="1234567890",
            correo_contacto="default@example.com",
            is_active=True
        )
        print(f"Tenant por defecto creado: {tenant.name}")
    except Exception as e:
        print(f"Error al crear tenant por defecto: {str(e)}")

if __name__ == "__main__":
    create_default_tenant() 