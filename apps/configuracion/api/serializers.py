# configuracion/api/serializers.py
from rest_framework import serializers
from ..models import TenantConfig, EmailConfig
from apps.tenants.models import Tenant
from apps.authentication.models import ZentraflowUser

class TenantSerializer(serializers.ModelSerializer):
    """Serializador para el modelo Tenant."""
    class Meta:
        model = Tenant
        fields = ['id', 'name', 'nit', 'domain', 'is_active']

class TenantConfigSerializer(serializers.ModelSerializer):
    """Serializer para el modelo TenantConfig."""
    tenant_name = serializers.SerializerMethodField()
    logo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = TenantConfig
        fields = ['id', 'tenant', 'tenant_name', 'timezone', 'date_format', 'logo_url', 'last_updated']
        read_only_fields = ['id', 'tenant', 'tenant_name', 'last_updated']
    
    def get_tenant_name(self, obj):
        """Obtiene el nombre del tenant."""
        return obj.tenant.name if obj.tenant else None
    
    def get_logo_url(self, obj):
        """Obtiene la URL del logo del tenant."""
        if obj.logo and hasattr(obj.logo, 'url'):
            return obj.logo.url
        return None

class EmailConfigSerializer(serializers.ModelSerializer):
    """Serializer para el modelo EmailConfig."""
    tenant_name = serializers.SerializerMethodField()
    
    class Meta:
        model = EmailConfig
        fields = [
            'id', 'tenant', 'tenant_name', 'email_address', 'protocol', 
            'server_host', 'server_port', 'username', 'use_ssl', 
            'folder_to_monitor', 'check_interval', 'mark_as_read', 
            'ingesta_enabled', 'last_check', 'connection_status', 
            'connection_error', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'tenant', 'tenant_name', 'last_check', 
                            'connection_status', 'connection_error', 
                            'created_at', 'updated_at']
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def get_tenant_name(self, obj):
        """Obtiene el nombre del tenant."""
        return obj.tenant.name if obj.tenant else None