from django.contrib import admin
from .models import TenantConfig, EmailOAuthCredentials

@admin.register(TenantConfig)
class TenantConfigAdmin(admin.ModelAdmin):
    """Administrador para las configuraciones de tenants."""
    list_display = ('tenant', 'timezone', 'date_format', 'last_updated', 'updated_by')
    search_fields = ('tenant__name', 'timezone')
    list_filter = ('timezone', 'date_format')
    readonly_fields = ('last_updated',)

@admin.register(EmailOAuthCredentials)
class EmailOAuthCredentialsAdmin(admin.ModelAdmin):
    """Administrador para las credenciales OAuth de correo electrónico."""
    list_display = ('tenant', 'email_address', 'authorized', 'last_authorized', 'ingesta_enabled')
    search_fields = ('tenant__name', 'email_address')
    list_filter = ('authorized', 'ingesta_enabled')
    readonly_fields = ('last_authorized', 'token_expiry')
    fieldsets = (
        ('Información del Tenant', {
            'fields': ('tenant', 'email_address')
        }),
        ('Configuración OAuth', {
            'fields': ('client_id', 'client_secret', 'redirect_uri')
        }),
        ('Estado de Autorización', {
            'fields': ('authorized', 'last_authorized', 'access_token', 'refresh_token', 'token_expiry')
        }),
        ('Configuración de Ingesta', {
            'fields': ('folder_to_monitor', 'check_interval', 'mark_as_read', 'ingesta_enabled')
        }),
    )