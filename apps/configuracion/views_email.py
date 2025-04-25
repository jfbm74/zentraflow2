from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import logging

from apps.tenants.models import Tenant
from .models import EmailConfig

# Configurar logger
logger = logging.getLogger(__name__)

@method_decorator(login_required, name='dispatch')
class EmailConfigView(View):
    """Vista para gestionar la configuración de correo."""
    
    def get(self, request, tenant_id=None):
        """Obtiene la configuración de correo actual."""
        try:
            # Determinar el tenant a usar
            if tenant_id and (request.user.is_superuser or request.user.role == 'ADMIN'):
                tenant = get_object_or_404(Tenant, id=tenant_id, is_active=True)
            else:
                tenant = request.user.tenant
            
            # Obtener configuración
            config = get_object_or_404(EmailConfig, tenant=tenant)
            
            # Devolver configuración
            return JsonResponse({
                'success': True,
                'config': {
                    'email_address': config.email_address,
                    'protocol': config.protocol,
                    'server_host': config.server_host,
                    'server_port': config.server_port,
                    'username': config.username,
                    'use_ssl': config.use_ssl,
                    'folder_to_monitor': config.folder_to_monitor,
                    'check_interval': config.check_interval,
                    'mark_as_read': config.mark_as_read,
                    'ingesta_enabled': config.ingesta_enabled,
                    'connection_status': config.connection_status,
                    'last_check': config.last_check.isoformat() if config.last_check else None
                }
            })
            
        except Exception as e:
            logger.error(f"Error al obtener configuración de correo: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f'Error al obtener configuración: {str(e)}'
            }, status=500)
    
    @method_decorator(csrf_exempt)
    def post(self, request, tenant_id=None):
        """Guarda o actualiza la configuración de correo."""
        try:
            # Determinar el tenant a usar
            if tenant_id and (request.user.is_superuser or request.user.role == 'ADMIN'):
                tenant = get_object_or_404(Tenant, id=tenant_id, is_active=True)
            else:
                tenant = request.user.tenant
            
            # Obtener datos
            data = request.POST
            action = data.get('action', 'save_email_config')
            
            # Obtener o crear configuración
            config, created = EmailConfig.objects.get_or_create(tenant=tenant)
            
            # Actualizar campos si se proporcionan
            if 'email_address' in data:
                config.email_address = data['email_address']
                config.username = data['email_address']  # Por defecto, usar email como username
            
            if 'protocol' in data:
                config.protocol = data['protocol']
            
            if 'server_host' in data:
                config.server_host = data['server_host']
            
            if 'server_port' in data:
                config.server_port = int(data['server_port'])
            
            if 'password' in data and data['password']:
                config.password = data['password']
            
            if 'use_ssl' in data:
                config.use_ssl = data['use_ssl'].lower() == 'true'
            
            if 'folder_to_monitor' in data:
                config.folder_to_monitor = data['folder_to_monitor']
            
            if 'check_interval' in data:
                config.check_interval = int(data['check_interval'])
            
            if 'mark_as_read' in data:
                config.mark_as_read = data['mark_as_read'].lower() == 'true'
            
            if 'ingesta_enabled' in data:
                config.ingesta_enabled = data['ingesta_enabled'].lower() == 'true'
            
            # Guardar cambios
            config.save()
            
            # Probar conexión si se solicita
            if action == 'test_connection':
                success, message = config.test_connection()
                if success:
                    config.refresh_from_db()  # Recargar para obtener el estado actualizado
                return JsonResponse({
                    'success': success,
                    'message': message,
                    'connection_status': config.connection_status
                })
            
            return JsonResponse({
                'success': True,
                'message': 'Configuración guardada correctamente'
            })
            
        except Exception as e:
            logger.error(f"Error al guardar configuración de correo: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f'Error al guardar configuración: {str(e)}'
            }, status=500)

@method_decorator(login_required, name='dispatch')
class TestConnectionView(View):
    """Vista para probar la conexión al servidor de correo."""
    
    def post(self, request, tenant_id=None):
        try:
            # Determinar el tenant a usar
            if tenant_id and (request.user.is_superuser or request.user.role == 'ADMIN'):
                tenant = get_object_or_404(Tenant, id=tenant_id, is_active=True)
            else:
                tenant = request.user.tenant
            
            # Obtener configuración
            config = get_object_or_404(EmailConfig, tenant=tenant)
            
            # Probar conexión
            success, message = config.test_connection()
            
            return JsonResponse({
                'success': success,
                'message': message,
                'connection_status': config.connection_status
            })
            
        except EmailConfig.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'No hay configuración de correo establecida'
            }, status=404)
        except Exception as e:
            logger.error(f"Error al probar conexión: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f'Error al probar conexión: {str(e)}'
            }, status=500) 