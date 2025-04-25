import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zentraflow.settings')
django.setup()

from apps.tenants.models import Tenant
from apps.authentication.models import ZentraflowUser

def create_admin_user():
    """Crea un usuario administrador."""
    try:
        # Obtener el tenant específico con ID 1
        tenant = Tenant.objects.get(id=1)
        if not tenant:
            print("Error: No se encontró el tenant con ID 1")
            return

        # Crear el usuario
        user = ZentraflowUser.objects.create_superuser(
            email='admin@ejemplo.com',
            tenant=tenant,
            password='123',
            first_name='Admin',
            last_name='Sistema',
            is_active=True
        )
        
        print(f"Usuario administrador creado exitosamente: {user.email}")
        
    except Tenant.DoesNotExist:
        print("Error: No se encontró el tenant con ID 1")
    except Exception as e:
        print(f"Error al crear usuario administrador: {str(e)}")

if __name__ == "__main__":
    create_admin_user() 