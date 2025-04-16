# Ruta: apps/configuracion/models.py
from django.db import models
from apps.core.storage import TenantFileSystemStorage
import os

def tenant_directory_path(instance, filename):
    """
    Ruta donde se almacenará el archivo, estructurada por tenant.
    Ejemplo: 'tenants/tenant_1/logos/logo.png'
    """
    # Asegurarnos de tener solo el nombre del archivo sin ruta
    filename = os.path.basename(filename)
    tenant_id = instance.tenant.id
    
    # Imprimir información de depuración
    print(f"Creando ruta para tenant_id={tenant_id}, filename={filename}")
    path = f'tenants/tenant_{tenant_id}/logos/{filename}'
    print(f"tenant_directory_path: Ruta final: {path}")
    
    return path
class TenantConfig(models.Model):
    """Configuración específica para cada tenant."""
    tenant = models.OneToOneField('tenants.Tenant', on_delete=models.CASCADE, related_name='config')
    timezone = models.CharField(max_length=50, default='America/Bogota')
    date_format = models.CharField(max_length=20, default='DD/MM/YYYY')
    
    # Utilizar el storage personalizado para el logo
    logo = models.ImageField(
        upload_to=tenant_directory_path, 
        storage=TenantFileSystemStorage(),
        null=True, 
        blank=True,
        verbose_name="Logo del cliente"
    )
    
    last_updated = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey('authentication.ZentraflowUser', on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"Configuración para {self.tenant.name}"
    
    class Meta:
        app_label = 'configuracion'  # Sin el prefijo 'apps.'
        verbose_name = "Configuración de Cliente"
        verbose_name_plural = "Configuraciones de Clientes"
        
    def save(self, *args, **kwargs):
        """Asegurar que cada tenant tenga una sola configuración."""
        # Comprobar si ya existe una configuración para este tenant
        if not self.pk:
            existing = TenantConfig.objects.filter(tenant=self.tenant).first()
            if existing:
                # Si ya existe, actualizar en lugar de crear uno nuevo
                self.pk = existing.pk
        super().save(*args, **kwargs)