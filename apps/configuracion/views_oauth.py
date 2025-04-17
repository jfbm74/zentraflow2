# apps/configuracion/views_oauth.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import logging

from apps.tenants.models import Tenant
from .models import EmailOAuthCredentials
from .services.oauth_service import OAuthService

# Configurar logger
logger = logging.getLogger(__name__)

@login_required
def oauth_authorize(request):
    """Inicia el flujo de autorización OAuth."""
    tenant_id = request.GET.get('tenant_id')
    
    logger.info(f"Inicio de flujo de autorización OAuth - Usuario: {request.user.username}, Tenant ID: {tenant_id}")
    
    # Determinar el tenant a usar
    if tenant_id and (request.user.is_superuser or request.user.role == 'ADMIN'):
        tenant = get_object_or_404(Tenant, id=tenant_id, is_active=True)
        logger.debug(f"Usando tenant específico: {tenant.name} (ID: {tenant.id})")
    else:
        tenant = request.user.tenant
        logger.debug(f"Usando tenant del usuario: {tenant.name} (ID: {tenant.id})")
    
    # Obtener credenciales OAuth
    credentials = OAuthService.get_oauth_credentials(tenant)
    
    # Generar URL de autorización
    auth_url, error = OAuthService.get_authorization_url(credentials, request)
    
    if error:
        logger.error(f"Error al generar URL de autorización: {error}")
        return JsonResponse({'success': False, 'message': error})
    
    logger.info(f"URL de autorización generada correctamente para tenant {tenant.id}")
    return JsonResponse({'success': True, 'auth_url': auth_url})

@login_required
def oauth_callback(request):
    """Maneja la redirección del servidor de autorización OAuth."""
    code = request.GET.get('code')
    state = request.GET.get('state')
    session_state = request.session.get('oauth_state')
    tenant_id = request.session.get('oauth_tenant_id')
    
    logger.info(f"Callback de OAuth recibido - Usuario: {request.user.username}, Tenant ID: {tenant_id}")
    
    # Limpiar variables de sesión
    request.session.pop('oauth_state', None)
    request.session.pop('oauth_tenant_id', None)
    
    if not all([code, state, session_state, tenant_id]):
        logger.error(f"Parámetros incompletos en callback OAuth - Code: {bool(code)}, State: {bool(state)}, Session State: {bool(session_state)}, Tenant ID: {bool(tenant_id)}")
        return render(request, 'configuracion/oauth_result.html', {
            'success': False,
            'message': 'Parámetros incompletos para completar la autorización.'
        })
    
    # Procesar callback
    success, message = OAuthService.handle_oauth_callback(code, state, session_state, tenant_id)
    
    if success:
        logger.info(f"Autorización OAuth completada con éxito para tenant {tenant_id}")
    else:
        logger.error(f"Error en autorización OAuth para tenant {tenant_id}: {message}")
    
    return render(request, 'configuracion/oauth_result.html', {
        'success': success,
        'message': message
    })

class OAuthStatusView(View):
    """Vista para verificar el estado de autorización OAuth."""
    
    @method_decorator(login_required)
    def get(self, request, tenant_id=None):
        logger.info(f"Verificando estado OAuth - Usuario: {request.user.username}, Tenant ID: {tenant_id}")
        
        # Determinar el tenant a usar
        if tenant_id and (request.user.is_superuser or request.user.role == 'ADMIN'):
            tenant = get_object_or_404(Tenant, id=tenant_id, is_active=True)
            logger.debug(f"Usando tenant específico: {tenant.name} (ID: {tenant.id})")
        else:
            tenant = request.user.tenant
            logger.debug(f"Usando tenant del usuario: {tenant.name} (ID: {tenant.id})")
        
        # Obtener credenciales OAuth
        credentials = OAuthService.get_oauth_credentials(tenant)
        logger.debug(f"Credenciales OAuth obtenidas para tenant {tenant.id}, email: {credentials.email_address}")
        
        # Verificar si está autorizado y el token es válido
        is_authorized = credentials.authorized
        is_token_valid = credentials.is_token_valid() if is_authorized else False
        logger.debug(f"Estado de autorización - Autorizado: {is_authorized}, Token válido: {is_token_valid}")
        
        # Si el token no es válido pero tenemos refresh token, intentar refrescarlo
        if is_authorized and not is_token_valid and credentials.refresh_token:
            logger.info(f"Intentando refrescar token expirado para tenant {tenant.id}")
            success, _ = OAuthService.refresh_access_token(credentials)
            is_token_valid = success
            logger.info(f"Resultado de refrescar token: {'Éxito' if success else 'Fallo'}")
        
        response_data = {
            'success': True,
            'authorized': is_authorized,
            'token_valid': is_token_valid,
            'email_address': credentials.email_address,
            'last_authorized': credentials.last_authorized.isoformat() if credentials.last_authorized else None,
            'folder_to_monitor': credentials.folder_to_monitor,
            'check_interval': credentials.check_interval,
            'mark_as_read': credentials.mark_as_read,
            'ingesta_enabled': getattr(credentials, 'ingesta_enabled', True)
        }
        
        logger.info(f"Enviando estado OAuth para tenant {tenant.id} - Autorizado: {is_authorized}, Token válido: {is_token_valid}")
        logger.debug(f"Datos de configuración - Carpeta: {credentials.folder_to_monitor}, Intervalo: {credentials.check_interval}, Marcar como leído: {credentials.mark_as_read}, Ingesta habilitada: {getattr(credentials, 'ingesta_enabled', True)}")
        
        return JsonResponse(response_data)

class OAuthRevokeView(View):
    """Vista para revocar la autorización OAuth."""
    
    @method_decorator(login_required)
    @method_decorator(csrf_exempt)
    def post(self, request, tenant_id=None):
        logger.info(f"Solicitud de revocación OAuth - Usuario: {request.user.username}, Tenant ID: {tenant_id}")
        
        # Determinar el tenant a usar
        if tenant_id and (request.user.is_superuser or request.user.role == 'ADMIN'):
            tenant = get_object_or_404(Tenant, id=tenant_id, is_active=True)
            logger.debug(f"Usando tenant específico para revocación: {tenant.name} (ID: {tenant.id})")
        else:
            tenant = request.user.tenant
            logger.debug(f"Usando tenant del usuario para revocación: {tenant.name} (ID: {tenant.id})")
        
        # Obtener credenciales OAuth
        credentials = OAuthService.get_oauth_credentials(tenant)
        logger.debug(f"Revocando acceso para email: {credentials.email_address}")
        
        # Revocar acceso
        success, message = OAuthService.revoke_access(credentials)
        
        if success:
            logger.info(f"Acceso OAuth revocado con éxito para tenant {tenant.id}")
        else:
            logger.error(f"Error al revocar acceso OAuth para tenant {tenant.id}: {message}")
        
        return JsonResponse({
            'success': success,
            'message': message
        })

class OAuthSettingsView(View):
    """Vista para actualizar la configuración de OAuth."""
    
    @method_decorator(login_required)
    @method_decorator(csrf_exempt)
    def post(self, request, tenant_id=None):
        logger.info(f"Guardando configuración OAuth - Usuario: {request.user.username}, Tenant ID: {tenant_id}")
        
        # Determinar el tenant a usar
        if tenant_id and (request.user.is_superuser or request.user.role == 'ADMIN'):
            tenant = get_object_or_404(Tenant, id=tenant_id, is_active=True)
            logger.debug(f"Usando tenant específico para configuración: {tenant.name} (ID: {tenant.id})")
        else:
            tenant = request.user.tenant
            logger.debug(f"Usando tenant del usuario para configuración: {tenant.name} (ID: {tenant.id})")
        
        # Verificar permisos
        if not (request.user.is_superuser or request.user.role == 'ADMIN'):
            logger.warning(f"Intento de modificar configuración OAuth sin permisos - Usuario: {request.user.username}")
            return JsonResponse({
                'success': False,
                'message': 'No tiene permisos para modificar la configuración OAuth.'
            }, status=403)
        
        # Obtener credenciales OAuth
        credentials = OAuthService.get_oauth_credentials(tenant)
        logger.debug(f"Credenciales OAuth obtenidas para tenant {tenant.id}, email: {credentials.email_address}")
        
        # Actualizar configuración
        try:
            # Obtener datos
            data = request.POST.dict()
            
            # Log de datos recibidos (sin exponer secret)
            safe_data = data.copy()
            if 'client_secret' in safe_data:
                safe_data['client_secret'] = '[REDACTADO]'
            
            logger.info(f"Actualizando configuración OAuth para tenant {tenant.id}")
            logger.debug(f"Datos recibidos para configuración OAuth: {safe_data}")
            
            # Debug: Imprimir datos recibidos
            print(f"OAuthSettingsView datos recibidos: {safe_data}")
            
            # Actualizar credenciales OAuth
            updated_fields = []
            
            if 'client_id' in data:
                credentials.client_id = data['client_id']
                updated_fields.append('client_id')
            
            if 'client_secret' in data:
                credentials.client_secret = data['client_secret']
                updated_fields.append('client_secret')
            
            if 'email_address' in data:
                old_email = credentials.email_address
                credentials.email_address = data['email_address']
                updated_fields.append('email_address')
                logger.debug(f"Cambiando email_address de '{old_email}' a '{data['email_address']}'")
            
            if 'folder_to_monitor' in data:
                old_folder = credentials.folder_to_monitor
                credentials.folder_to_monitor = data['folder_to_monitor']
                updated_fields.append('folder_to_monitor')
                logger.debug(f"Cambiando folder_to_monitor de '{old_folder}' a '{data['folder_to_monitor']}'")
            
            if 'check_interval' in data:
                old_interval = credentials.check_interval
                credentials.check_interval = int(data['check_interval'])
                updated_fields.append('check_interval')
                logger.debug(f"Cambiando check_interval de {old_interval} a {data['check_interval']}")
            
            if 'mark_as_read' in data:
                old_value = credentials.mark_as_read
                new_value = data['mark_as_read'].lower() == 'true'
                credentials.mark_as_read = new_value
                updated_fields.append('mark_as_read')
                logger.debug(f"Cambiando mark_as_read de {old_value} a {new_value}")
            
            if 'ingesta_enabled' in data:
                old_value = getattr(credentials, 'ingesta_enabled', True)
                new_value = data['ingesta_enabled'].lower() == 'true'
                credentials.ingesta_enabled = new_value
                updated_fields.append('ingesta_enabled')
                logger.debug(f"Cambiando ingesta_enabled de {old_value} a {new_value}")
            
            # Si cambiamos client_id o client_secret, revocar autorización actual
            if 'client_id' in data or 'client_secret' in data:
                logger.info(f"Credenciales OAuth modificadas para tenant {tenant.id}, revocando autorización actual")
                credentials.authorized = False
                credentials.access_token = None
                credentials.refresh_token = None
                credentials.token_expiry = None
                updated_fields.append('autorización (revocada)')
            
            logger.info(f"Campos actualizados: {', '.join(updated_fields)}")
            
            credentials.save()
            logger.info(f"Configuración OAuth guardada correctamente para tenant {tenant.id}")
            
            return JsonResponse({
                'success': True,
                'message': 'Configuración OAuth actualizada correctamente.'
            })
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error al actualizar configuración OAuth para tenant {tenant.id}: {error_msg}", exc_info=True)
            print(f"Error al actualizar configuración OAuth: {error_msg}")
            
            return JsonResponse({
                'success': False,
                'message': f'Error al actualizar la configuración OAuth: {error_msg}'
            }, status=400)