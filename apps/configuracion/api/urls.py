# configuracion/api/__init__.py
# Este archivo puede estar vacío, solo se requiere para que Python reconozca el directorio como un paquete

# configuracion/api/urls.py
from django.urls import path
from .views import TenantConfigAPIView, EmailConfigAPIView

urlpatterns = [
    path('tenant/', TenantConfigAPIView.as_view(), name='api_tenant_config'),
    path('tenant/<int:tenant_id>/', TenantConfigAPIView.as_view(), name='api_tenant_config_detail'),
    path('email-config/', EmailConfigAPIView.as_view(), name='api_email_config'),
    path('email-config/<int:tenant_id>/', EmailConfigAPIView.as_view(), name='api_email_config_detail'),
]