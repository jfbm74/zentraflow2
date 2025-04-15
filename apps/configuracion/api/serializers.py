# configuracion/api/serializers.py
from rest_framework import serializers
from tenants.models import Tenant
from ..models import TenantConfig

class TenantSerializer(serializers.ModelSerializer):
    """Serializador para el modelo Tenant."""
    class Meta:
        model = Tenant
        fields = ['id', 'name', 'nit', 'domain', 'is_active']

class TenantConfigSerializer(serializers.ModelSerializer):
    """Serializador para el modelo TenantConfig."""
    tenant = TenantSerializer(read_only=True)
    logo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = TenantConfig
        fields = ['id', 'tenant', 'timezone', 'date_format', 'logo', 'logo_url', 'last_updated']
        read_only_fields = ['id', 'tenant', 'logo_url', 'last_updated']
    
    def get_logo_url(self, obj):
        """Obtiene la URL del logo si existe."""
        if obj.logo:
            return obj.logo.url
        return None