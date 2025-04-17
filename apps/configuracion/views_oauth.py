# apps/configuracion/views_oauth.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View

from apps.tenants.models import Tenant
from .models import EmailOAuthCredentials
from .services.oauth_service import OAuthService

@login_required
def oauth_authorize(request):
    """Inicia el flujo de autorización OAuth."""
    tenant_id = request.GET.get('tenant_id')
    
    # Determinar el tenant a usar
    if tenant_id and (request.user.is_superuser or request.user.role == 'ADMIN'):
        tenant = get_object_or_404(Tenant, id=tenant_id, is_active=True)
    else:
        tenant = request.user.tenant
    
    # Obtener credenciales OAuth
    credentials = OAuthService.get_oauth_credentials(tenant)
    
    # Generar URL de autorización
    auth_url, error = OAuthService.get_authorization_url(credentials, request)
    
    if error:
        return JsonResponse({'success': False, 'message': error})
    
    return JsonResponse({'success': True, 'auth_url': auth_url})

@login_required
def oauth_callback(request):
    """Maneja la redirección del servidor de autorización OAuth."""
    code = request.GET.get('code')
    state = request.GET.get('state')
    session_state = request.session.get('oauth_state')
    tenant_id = request.session.get('oauth_tenant_id')
    
    # Limpiar variables de sesión
    request.session.pop('oauth_state', None)
    request.session.pop('oauth_tenant_id', None)
    
    if not all([code, state, session_state, tenant_id]):
        return render(request, 'configuracion/oauth_result.html', {
            'success': False,
            'message': 'Parámetros incompletos para completar la autorización.'
        })
    
    # Procesar callback
    success, message = OAuthService.handle_oauth_callback(code, state, session_state, tenant_id)
    
    return render(request, 'configuracion/oauth_result.html', {
        'success': success,
        'message': message
    })

class OAuthStatusView(View):
    """Vista para verificar el estado de autorización OAuth."""
    
    @method_decorator(login_required)
    def get(self, request, tenant_id=None):
        # Determinar el tenant a usar
        if tenant_id and (request.user.is_superuser or request.user.role == 'ADMIN'):
            tenant = get_object_or_404(Tenant, id=tenant_id, is_active=True)
        else:
            tenant = request.user.tenant
        
        # Obtener credenciales OAuth
        credentials = OAuthService.get_oauth_credentials(tenant)
        
        # Verificar si está autorizado y el token es válido
        is_authorized = credentials.authorized
        is_token_valid = credentials.is_token_valid() if is_authorized else False
        
        # Si el token no es válido pero tenemos refresh token, intentar refrescarlo
        if is_authorized and not is_token_valid and credentials.refresh_token:
            success, _ = OAuthService.refresh_access_token(credentials)
            is_token_valid = success
        
        return JsonResponse({
            'success': True,
            'authorized': is_authorized,
            'token_valid': is_token_valid,
            'email_address': credentials.email_address,
            'last_authorized': credentials.last_authorized.isoformat() if credentials.last_authorized else None,
            'folder_to_monitor': credentials.folder_to_monitor,
            'check_interval': credentials.check_interval,
            'mark_as_read': credentials.mark_as_read,
            'ingesta_enabled': getattr(credentials, 'ingesta_enabled', True)
        })

class OAuthRevokeView(View):
    """Vista para revocar la autorización OAuth."""
    
    @method_decorator(login_required)
    @method_decorator(csrf_exempt)
    def post(self, request, tenant_id=None):
        # Determinar el tenant a usar
        if tenant_id and (request.user.is_superuser or request.user.role == 'ADMIN'):
            tenant = get_object_or_404(Tenant, id=tenant_id, is_active=True)
        else:
            tenant = request.user.tenant
        
        # Obtener credenciales OAuth
        credentials = OAuthService.get_oauth_credentials(tenant)
        
        # Revocar acceso
        success, message = OAuthService.revoke_access(credentials)
        
        return JsonResponse({
            'success': success,
            'message': message
        })

class OAuthSettingsView(View):
    """Vista para actualizar la configuración de OAuth."""
    
    @method_decorator(login_required)
    @method_decorator(csrf_exempt)
    def post(self, request, tenant_id=None):
        # Determinar el tenant a usar
        if tenant_id and (request.user.is_superuser or request.user.role == 'ADMIN'):
            tenant = get_object_or_404(Tenant, id=tenant_id, is_active=True)
        else:
            tenant = request.user.tenant
        
        # Verificar permisos
        if not (request.user.is_superuser or request.user.role == 'ADMIN'):
            return JsonResponse({
                'success': False,
                'message': 'No tiene permisos para modificar la configuración OAuth.'
            }, status=403)
        
        # Obtener credenciales OAuth
        credentials = OAuthService.get_oauth_credentials(tenant)
        
        # Actualizar configuración
        try:
            # Obtener datos
            data = request.POST.dict()
            
            # Debug: Imprimir datos recibidos
            print(f"OAuthSettingsView datos recibidos: {data}")
            
            # Actualizar credenciales OAuth
            if 'client_id' in data:
                credentials.client_id = data['client_id']
            if 'client_secret' in data:
                credentials.client_secret = data['client_secret']
            if 'email_address' in data:
                credentials.email_address = data['email_address']
            if 'folder_to_monitor' in data:
                credentials.folder_to_monitor = data['folder_to_monitor']
            if 'check_interval' in data:
                credentials.check_interval = int(data['check_interval'])
            if 'mark_as_read' in data:
                credentials.mark_as_read = data['mark_as_read'].lower() == 'true'
            if 'ingesta_enabled' in data:
                credentials.ingesta_enabled = data['ingesta_enabled'].lower() == 'true'
            
            # Si cambiamos client_id o client_secret, revocar autorización actual
            if 'client_id' in data or 'client_secret' in data:
                credentials.authorized = False
                credentials.access_token = None
                credentials.refresh_token = None
                credentials.token_expiry = None
            
            credentials.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Configuración OAuth actualizada correctamente.'
            })
            
        except Exception as e:
            print(f"Error al actualizar configuración OAuth: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f'Error al actualizar la configuración OAuth: {str(e)}'
            }, status=400)