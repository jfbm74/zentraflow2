from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import ZentraflowUser

@admin.register(ZentraflowUser)
class ZentraflowUserAdmin(UserAdmin):
    """Configuración admin para el modelo ZentraflowUser."""
    list_display = ('email', 'first_name', 'last_name', 'tenant', 'role', 'is_active', 'is_locked')
    list_filter = ('is_active', 'is_locked', 'role', 'tenant')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Información personal', {'fields': ('first_name', 'last_name')}),
        ('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser', 'is_locked', 'groups', 'user_permissions')}),
        ('Tenant y Rol', {'fields': ('tenant', 'role')}),
        ('Fechas importantes', {'fields': ('last_login', 'date_joined')}),
        ('Seguridad', {'fields': ('last_login_ip', 'failed_login_attempts')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'tenant', 'role'),
        }),
    )