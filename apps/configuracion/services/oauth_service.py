# apps/configuracion/services/oauth_service.py
import datetime
import json
import uuid
from django.utils import timezone
from django.conf import settings
from django.urls import reverse
import requests

from ..models import EmailOAuthCredentials

class OAuthService:
    """Servicio para manejar la autenticación OAuth 2.0 para cuentas de correo."""

    @staticmethod
    def get_oauth_credentials(tenant):
        """Obtiene o crea las credenciales OAuth para un tenant."""
        credentials, created = EmailOAuthCredentials.objects.get_or_create(tenant=tenant)
        return credentials
    
    @staticmethod
    def get_authorization_url(credentials, request):
        """Genera una URL para iniciar el flujo de autorización OAuth 2.0."""
        if not credentials.client_id or not credentials.client_secret:
            return None, "Las credenciales OAuth no están configuradas correctamente."
        
        # Generar un state aleatorio para evitar CSRF
        state = str(uuid.uuid4())
        request.session['oauth_state'] = state
        
        # Guardar también el tenant_id en la sesión
        request.session['oauth_tenant_id'] = credentials.tenant.id
        
        # Configurar redirect_uri
        scheme = 'https' if request.is_secure() else 'http'
        host = request.get_host()
        redirect_uri = f"{scheme}://{host}{reverse('oauth_callback')}"
        
        # Guardar redirect_uri en el modelo
        credentials.redirect_uri = redirect_uri
        credentials.save()
        
        # Construir URL de autorización
        params = {
            'client_id': credentials.client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': 'https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/gmail.modify',
            'access_type': 'offline',
            'prompt': 'consent',  # Para asegurar que recibimos refresh_token
            'state': state
        }
        
        # Construir la URL con los parámetros
        auth_url = "https://accounts.google.com/o/oauth2/auth?"
        auth_url += "&".join([f"{key}={requests.utils.quote(value)}" for key, value in params.items()])
        
        return auth_url, None
    
    @staticmethod
    def handle_oauth_callback(code, state, session_state, tenant_id):
        """Procesa la respuesta del servidor de autorización OAuth."""
        # Verificar estado para prevenir CSRF
        if state != session_state:
            return False, "Error de seguridad: el estado no coincide."
        
        # Obtener credenciales del tenant
        try:
            credentials = EmailOAuthCredentials.objects.get(tenant_id=tenant_id)
        except EmailOAuthCredentials.DoesNotExist:
            return False, "No se encontraron las credenciales para el tenant especificado."
        
        # Intercambiar código de autorización por tokens
        token_url = "https://oauth2.googleapis.com/token"
        data = {
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'code': code,
            'redirect_uri': credentials.redirect_uri,
            'grant_type': 'authorization_code'
        }
        
        response = requests.post(token_url, data=data)
        
        if response.status_code != 200:
            return False, f"Error al obtener tokens: {response.text}"
        
        # Procesar la respuesta
        token_data = response.json()
        credentials.access_token = token_data.get('access_token')
        credentials.refresh_token = token_data.get('refresh_token', credentials.refresh_token)
        
        # Calcular expiración del token
        expires_in = token_data.get('expires_in', 3600)  # Por defecto 1 hora
        credentials.token_expiry = timezone.now() + datetime.timedelta(seconds=expires_in)
        
        # Marcar como autorizado
        credentials.authorized = True
        credentials.last_authorized = timezone.now()
        
        # Obtener el email de la cuenta
        if credentials.access_token:
            credentials.email_address = OAuthService.get_user_email(credentials.access_token)
        
        credentials.save()
        
        return True, "Autorización completada con éxito."
    
    @staticmethod
    def get_user_email(access_token):
        """Obtiene la dirección de correo del usuario usando el token de acceso."""
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(
            "https://www.googleapis.com/gmail/v1/users/me/profile",
            headers=headers
        )
        
        if response.status_code == 200:
            return response.json().get('emailAddress')
        return None
    
    @staticmethod
    def refresh_access_token(credentials):
        """Refresca el token de acceso usando el refresh token."""
        if not credentials.refresh_token:
            return False, "No hay refresh token disponible."
        
        token_url = "https://oauth2.googleapis.com/token"
        data = {
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'refresh_token': credentials.refresh_token,
            'grant_type': 'refresh_token'
        }
        
        response = requests.post(token_url, data=data)
        
        if response.status_code != 200:
            credentials.authorized = False
            credentials.save()
            return False, f"Error al refrescar el token: {response.text}"
        
        # Procesar la respuesta
        token_data = response.json()
        credentials.access_token = token_data.get('access_token')
        
        # Calcular expiración del token
        expires_in = token_data.get('expires_in', 3600)  # Por defecto 1 hora
        credentials.token_expiry = timezone.now() + datetime.timedelta(seconds=expires_in)
        
        credentials.save()
        
        return True, "Token refrescado con éxito."
    
    @staticmethod
    def revoke_access(credentials):
        """Revoca el acceso OAuth y limpia los tokens."""
        if credentials.access_token:
            revoke_url = f"https://oauth2.googleapis.com/revoke?token={credentials.access_token}"
            requests.post(revoke_url)
        
        # Limpiar tokens y estado
        credentials.access_token = None
        credentials.refresh_token = None
        credentials.token_expiry = None
        credentials.authorized = False
        credentials.save()
        
        return True, "Acceso revocado correctamente."