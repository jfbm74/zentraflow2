import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zentraflow.settings')
django.setup()

from apps.tenants.models import Tenant

tenant = Tenant.objects.first()
print(tenant.id) 