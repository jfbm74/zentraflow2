from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from ipware import get_client_ip
from apps.authentication.models import ZentraflowUser  # Update this



class AuthenticationService:
    """Servicio para manejar la autenticación de usuarios."""
    
    @staticmethod
    def authenticate_user(request, email, password):
        """Autenticar usuario con email y contraseña."""
        client_ip, _ = get_client_ip(request)
        
        try:
            user = ZentraflowUser.objects.get(email=email)
            
            # Verificar si la cuenta está bloqueada
            if user.is_locked:
                return {
                    'success': False,
                    'message': 'Su cuenta ha sido bloqueada debido a múltiples intentos fallidos.',
                    'error_code': 'account_locked'
                }
            
            # Intentar autenticar
            user_auth = authenticate(request, email=email, password=password)
            
            if user_auth is not None:
                # Autenticación exitosa
                user.last_login_ip = client_ip
                user.failed_login_attempts = 0
                user.is_locked = False
                user.save()
                
                return {
                    'success': True,
                    'user': user_auth
                }
            else:
                # Autenticación fallida
                user.failed_login_attempts += 1
                
                # Bloquear cuenta después de 5 intentos fallidos
                if user.failed_login_attempts >= 5:
                    user.is_locked = True
                
                user.save()
                
                error_msg = 'Credenciales inválidas. Por favor, intente nuevamente.'
                if user.is_locked:
                    error_msg = 'Su cuenta ha sido bloqueada debido a múltiples intentos fallidos.'
                
                return {
                    'success': False,
                    'message': error_msg,
                    'error_code': 'invalid_credentials' if not user.is_locked else 'account_locked'
                }
                
        except ZentraflowUser.DoesNotExist:
            # No revelamos si el usuario existe o no por razones de seguridad
            return {
                'success': False,
                'message': 'Credenciales inválidas. Por favor, intente nuevamente.',
                'error_code': 'invalid_credentials'
            }
    
    @staticmethod
    def get_tokens_for_user(user):
        """Generar tokens JWT para un usuario autenticado."""
        refresh = RefreshToken.for_user(user)
        
        # Agregar claims personalizados al token
        refresh['tenant_id'] = user.tenant.id
        refresh['role'] = user.role
        refresh['name'] = user.full_name
        
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }