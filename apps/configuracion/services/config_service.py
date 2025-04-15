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

# En apps/configuracion/services/config_service.py
    @staticmethod
    def update_tenant_config(tenant, user, data, files=None):
        """
        Actualiza la configuración de un tenant.
        """
        try:
            print("===== Iniciando actualización de configuración =====")
            print(f"Tenant: {tenant.name} (ID: {tenant.id})")
            print(f"Usuario: {user.email}")
            print(f"Datos recibidos: {data}")
            if files:
                print(f"Archivos recibidos: {list(files.keys())}")
            
            # Actualizar datos del tenant
            if 'name' in data and data['name']:
                tenant.name = data['name']
            if 'nit' in data and data['nit']:
                tenant.nit = data['nit']
            tenant.save()
            
            # Obtener o crear la configuración
            config = ConfigService.get_tenant_config(tenant)
            print(f"Configuración obtenida: ID {config.id}")
            
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
                    print(f"Procesando logo: {logo_file.name}, tamaño: {logo_file.size} bytes")
                    
                    # Si ya existe un logo, eliminarlo
                    if config.logo:
                        try:
                            if os.path.exists(config.logo.path):
                                print(f"Eliminando logo anterior: {config.logo.path}")
                                os.remove(config.logo.path)
                            else:
                                print(f"Logo anterior no encontrado en: {config.logo.path}")
                        except Exception as e:
                            print(f"Error al eliminar logo anterior: {e}")
                    
                    # Guardar el nuevo logo
                    config.logo = logo_file
                    print(f"Logo asignado: {logo_file.name}")
            
            # Guardar cambios
            config.save()
            print("Configuración guardada")
            
            # Verificar que el logo se guardó correctamente
            if files and 'logo' in files and config.logo:
                try:
                    print(f"Path del logo guardado: {config.logo.path}")
                    print(f"URL del logo: {config.logo.url}")
                    if os.path.exists(config.logo.path):
                        print(f"Verificación: El archivo existe en {config.logo.path}")
                    else:
                        print(f"ADVERTENCIA: El archivo no existe en {config.logo.path}")
                except Exception as e:
                    print(f"Error al verificar el logo guardado: {e}")
            
            print("===== Actualización de configuración completada =====")
            return {
                'success': True,
                'message': 'Configuración actualizada correctamente.'
            }
        except Exception as e:
            import traceback
            print(f"ERROR: {str(e)}")
            print(traceback.format_exc())
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