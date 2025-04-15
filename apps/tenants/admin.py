from django.contrib import admin
from .models import Tenant

@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    """Configuración admin para el modelo Tenant."""
    list_display = ('name', 'domain', 'created_at', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'domain')
    ordering = ('name',)