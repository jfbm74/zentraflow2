from django.contrib import admin
from .models import TenantConfig, EmailConfig

@admin.register(TenantConfig)
class TenantConfigAdmin(admin.ModelAdmin):
    """Administrador para las configuraciones de tenants."""
    list_display = ('tenant', 'timezone', 'date_format', 'last_updated', 'updated_by')
    search_fields = ('tenant__name', 'timezone')
    list_filter = ('timezone', 'date_format')
    readonly_fields = ('last_updated',)

@admin.register(EmailConfig)
class EmailConfigAdmin(admin.ModelAdmin):
    """Administrador para la configuración de correo."""
    list_display = ('tenant', 'email_address', 'protocol', 'server_host', 'connection_status', 'ingesta_enabled')
    search_fields = ('tenant__name', 'email_address', 'server_host')
    list_filter = ('protocol', 'connection_status', 'ingesta_enabled', 'use_ssl')
    readonly_fields = ('connection_status', 'connection_error', 'last_check', 'created_at', 'updated_at')
    fieldsets = (
        ('Información del Tenant', {
            'fields': ('tenant', 'email_address')
        }),
        ('Configuración del Servidor', {
            'fields': ('protocol', 'server_host', 'server_port', 'username', 'password', 'use_ssl')
        }),
        ('Configuración de Ingesta', {
            'fields': ('folder_to_monitor', 'check_interval', 'mark_as_read', 'ingesta_enabled')
        }),
        ('Estado de Conexión', {
            'fields': ('connection_status', 'connection_error', 'last_check', 'created_at', 'updated_at')
        }),
    )