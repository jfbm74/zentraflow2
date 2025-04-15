# configuracion/api/__init__.py
# Este archivo puede estar vacío, solo se requiere para que Python reconozca el directorio como un paquete

# configuracion/api/urls.py
from django.urls import path
from .views import TenantConfigAPIView

urlpatterns = [
    path('tenant/', TenantConfigAPIView.as_view(), name='api_tenant_config'),
    path('tenant/<int:tenant_id>/', TenantConfigAPIView.as_view(), name='api_tenant_config_detail'),
]