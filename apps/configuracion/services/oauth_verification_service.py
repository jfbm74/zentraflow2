from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class OAuthVerificationService:
    """
    Servicio para verificar y gestionar conexiones OAuth para ingesta de correo.
    """
    
    @staticmethod
    def verify_connection(tenant):
        """
        Verifica el estado de la conexión OAuth para un tenant.
        
        Args:
            tenant: Objeto Tenant para verificar
            
        Returns:
            dict: Resultado de la verificación con el estado
        """
        try:
            # Intentar obtener las credenciales OAuth del tenant
            oauth_credentials = getattr(tenant, 'oauth_credentials', None)
            
            if not oauth_credentials:
                logger.info(f"Tenant {tenant.id}: No tiene credenciales OAuth configuradas")
                return {
                    'success': False,
                    'status': 'not_configured',
                    'message': 'No hay credenciales OAuth configuradas'
                }
            
            # Verificar si las credenciales están autorizadas
            if not oauth_credentials.authorized:
                logger.info(f"Tenant {tenant.id}: OAuth no autorizado")
                return {
                    'success': False,
                    'status': 'unauthorized',
                    'message': 'Autorización OAuth pendiente'
                }
            
            # Verificar si el token ha expirado
            if oauth_credentials.token_expiry and oauth_credentials.token_expiry < datetime.now():
                # Intentar refrescar el token
                refresh_result = OAuthVerificationService.refresh_token(oauth_credentials)
                if not refresh_result['success']:
                    logger.warning(f"Tenant {tenant.id}: Token expirado y no se pudo refrescar")
                    return {
                        'success': False,
                        'status': 'token_expired',
                        'message': 'El token expiró y no se pudo refrescar'
                    }
            
            # Verificar si la dirección de correo está configurada
            if not oauth_credentials.email_address:
                logger.info(f"Tenant {tenant.id}: Dirección de correo no configurada")
                return {
                    'success': False,
                    'status': 'email_not_configured',
                    'message': 'Dirección de correo no configurada'
                }
            
            # Todo parece estar bien
            logger.info(f"Tenant {tenant.id}: OAuth verificado correctamente")
            return {
                'success': True,
                'status': 'authorized',
                'message': 'Conexión OAuth verificada',
                'expires_in': OAuthVerificationService._get_expiry_time_remaining(oauth_credentials)
            }
            
        except Exception as e:
            logger.error(f"Error al verificar OAuth para tenant {tenant.id}: {str(e)}")
            return {
                'success': False,
                'status': 'error',
                'message': f'Error al verificar conexión: {str(e)}'
            }
    
    @staticmethod
    def refresh_token(oauth_credentials):
        """
        Intenta refrescar el token OAuth usando el refresh_token.
        
        Args:
            oauth_credentials: Objeto EmailOAuthCredentials
            
        Returns:
            dict: Resultado del intento de refrescar el token
        """
        try:
            # Aquí iría la lógica para refrescar el token usando la API correspondiente
            # (Google, Microsoft, etc.) utilizando el refresh_token
            
            # Por ahora, simulamos un error ya que la implementación real dependería
            # del proveedor OAuth específico
            logger.warning(f"Refresh token no implementado para las credenciales ID: {oauth_credentials.id}")
            return {
                'success': False,
                'message': 'Refresh token no implementado'
            }
        except Exception as e:
            logger.error(f"Error al refrescar token: {str(e)}")
            return {
                'success': False,
                'message': f'Error al refrescar token: {str(e)}'
            }
    
    @staticmethod
    def _get_expiry_time_remaining(oauth_credentials):
        """
        Calcula el tiempo restante hasta que expire el token.
        
        Args:
            oauth_credentials: Objeto EmailOAuthCredentials
            
        Returns:
            int: Segundos restantes hasta la expiración, o 0 si ya expiró
        """
        if not oauth_credentials.token_expiry:
            return 0
            
        now = datetime.now()
        if oauth_credentials.token_expiry <= now:
            return 0
            
        delta = oauth_credentials.token_expiry - now
        return int(delta.total_seconds()) 