# apps/configuracion/services/config_service.py
import os
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from ..models import TenantConfig

class ConfigService:
    """Servicio para operaciones relacionadas con la configuración del tenant."""
    
    @staticmethod
    def get_tenant_config(tenant):
        """Obtiene o crea la configuración para un tenant."""
        config, created = TenantConfig.objects.get_or_create(tenant=tenant)
        return config
    
    @staticmethod
    def update_tenant_config(tenant, user, data, files=None):
        """
        Actualiza la configuración de un tenant.
        
        Args:
            tenant: El objeto Tenant a actualizar.
            user: Usuario que realiza la actualización.
            data: Diccionario con datos de configuración.
            files: Diccionario con archivos (opcional).
            
        Returns:
            dict: Resultado de la operación.
        """
        try:
            # Actualizar datos del tenant
            if 'name' in data and data['name']:
                tenant.name = data['name']
            if 'nit' in data and data['nit']:
                tenant.nit = data['nit']
            tenant.save()
            
            # Obtener o crear la configuración
            config = ConfigService.get_tenant_config(tenant)
            
            # Actualizar configuración
            if 'timezone' in data and data['timezone']:
                config.timezone = data['timezone']
            if 'date_format' in data and data['date_format']:
                config.date_format = data['date_format']
            
            # Actualizar usuario que realizó cambios
            config.updated_by = user
            
            # Procesar logo si se proporciona
            if files and 'logo' in files:
                logo_file = files['logo']
                if logo_file:
                    # Si ya existe un logo, eliminarlo
                    if config.logo:
                        if os.path.exists(config.logo.path):
                            os.remove(config.logo.path)
                    config.logo = logo_file
            
            # Guardar cambios
            config.save()
            
            return {
                'success': True,
                'message': 'Configuración actualizada correctamente.'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error al actualizar la configuración: {str(e)}'
            }
    
    @staticmethod
    def remove_tenant_logo(tenant_config):
        """Elimina el logo de un tenant."""
        try:
            if tenant_config.logo:
                if os.path.exists(tenant_config.logo.path):
                    os.remove(tenant_config.logo.path)
                tenant_config.logo = None
                tenant_config.save()
                return {'success': True, 'message': 'Logo eliminado correctamente.'}
            return {'success': True, 'message': 'No hay logo para eliminar.'}
        except Exception as e:
            return {'success': False, 'message': f'Error al eliminar el logo: {str(e)}'}