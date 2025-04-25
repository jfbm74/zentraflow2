import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zentraflow.settings')
django.setup()

from apps.tenants.models import Tenant
from apps.authentication.models import ZentraflowUser

# Crear tenant
tenant = Tenant.objects.create(
    name="Cliente Principal",
    domain="principal.zentratek.com",
    nit="123456789",
    direccion="Calle Principal #123",
    telefono="123-456-7890",
    correo_contacto="contacto@principal.zentratek.com"
)

# Crear superusuario
ZentraflowUser.objects.create_superuser(
    email="admin@ejemplo.com",
    tenant=tenant,
    password="123",
    first_name="Admin",
    last_name="Sistema"
)

print(f"Tenant creado con ID: {tenant.id}")
print(f"Superusuario creado: admin@ejemplo.com")