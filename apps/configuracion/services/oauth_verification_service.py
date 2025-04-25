# apps/configuracion/services/oauth_verification_service.py
import logging
import requests
from django.utils import timezone
from ..models import EmailOAuthCredentials
from apps.ingesta_correo.models import ServicioIngesta, LogActividad

logger = logging.getLogger(__name__)

class OAuthVerificationService:
    """Servicio para verificar la conexión OAuth con Gmail."""

    @staticmethod
    def verify_connection(tenant):
        """
        Verifica la conexión OAuth con Gmail para un tenant específico.
        
        Args:
            tenant: El tenant para el que se verificará la conexión
            
        Returns:
            dict: Resultado de la verificación con los siguientes campos:
                - success (bool): Si la verificación fue exitosa
                - message (str): Mensaje descriptivo del resultado
                - status (dict): Estado detallado de cada componente verificado
        """
        try:
            # Obtener credenciales OAuth
            credentials = EmailOAuthCredentials.objects.filter(tenant=tenant).first()
            
            if not credentials:
                logger.warning(f"No se encontraron credenciales OAuth para el tenant {tenant.id}")
                return {
                    'success': False,
                    'message': 'No se ha configurado la conexión OAuth',
                    'status': {
                        'oauth_authorized': False,
                        'oauth_token_valid': False,
                        'folder_accessible': False,
                        'read_permissions': False,
                        'email_address': None
                    }
                }
            
            # Verificar si está autorizado
            if not credentials.authorized:
                logger.warning(f"Credenciales OAuth no autorizadas para el tenant {tenant.id}")
                return {
                    'success': False,
                    'message': 'La cuenta no está autorizada con OAuth',
                    'status': {
                        'oauth_authorized': False,
                        'oauth_token_valid': False,
                        'folder_accessible': False,
                        'read_permissions': False,
                        'email_address': credentials.email_address
                    }
                }
            
            # Verificar si el token es válido
            token_valid = credentials.is_token_valid()
            
            # Si el token no es válido pero tenemos refresh token, intentar refrescarlo
            if not token_valid and credentials.refresh_token:
                logger.info(f"Intentando refrescar token para tenant {tenant.id}")
                try:
                    from .oauth_service import OAuthService
                    refresh_success, message = OAuthService.refresh_access_token(credentials)
                    token_valid = refresh_success
                    
                    if not refresh_success:
                        logger.error(f"Error al refrescar token: {message}")
                        return {
                            'success': False,
                            'message': 'Error al refrescar token de acceso: ' + message,
                            'status': {
                                'oauth_authorized': True,
                                'oauth_token_valid': False,
                                'folder_accessible': False,
                                'read_permissions': False,
                                'email_address': credentials.email_address
                            }
                        }
                except Exception as e:
                    logger.exception(f"Excepción al refrescar token: {str(e)}")
                    return {
                        'success': False,
                        'message': f'Error al refrescar token de acceso: {str(e)}',
                        'status': {
                            'oauth_authorized': True,
                            'oauth_token_valid': False,
                            'folder_accessible': False,
                            'read_permissions': False,
                            'email_address': credentials.email_address
                        }
                    }
            
            if not token_valid:
                logger.warning(f"Token OAuth inválido para tenant {tenant.id}")
                return {
                    'success': False,
                    'message': 'El token de acceso no es válido y no se pudo refrescar',
                    'status': {
                        'oauth_authorized': True,
                        'oauth_token_valid': False,
                        'folder_accessible': False,
                        'read_permissions': False,
                        'email_address': credentials.email_address
                    }
                }
            
            # Verificar acceso a carpeta configurada
            folder_check = OAuthVerificationService.verify_folder_access(
                credentials.access_token, 
                credentials.email_address,
                credentials.folder_to_monitor
            )
            
            if not folder_check['success']:
                logger.warning(f"Error al verificar carpeta: {folder_check['message']}")
                return {
                    'success': False,
                    'message': folder_check['message'],
                    'status': {
                        'oauth_authorized': True,
                        'oauth_token_valid': True,
                        'folder_accessible': False,
                        'read_permissions': folder_check.get('has_read_permissions', False),
                        'email_address': credentials.email_address
                    }
                }
            
            # Todo correcto, actualizar el estado del servicio de ingesta
            OAuthVerificationService.update_service_status(tenant, credentials)
            
            logger.info(f"Verificación de conexión OAuth exitosa para tenant {tenant.id}")
            return {
                'success': True,
                'message': 'Conexión verificada correctamente',
                'status': {
                    'oauth_authorized': True,
                    'oauth_token_valid': True,
                    'folder_accessible': True,
                    'read_permissions': True,
                    'email_address': credentials.email_address
                }
            }
            
        except Exception as e:
            logger.exception(f"Error en verificación de conexión OAuth: {str(e)}")
            return {
                'success': False,
                'message': f'Error en la verificación: {str(e)}',
                'status': {
                    'oauth_authorized': False,
                    'oauth_token_valid': False,
                    'folder_accessible': False,
                    'read_permissions': False,
                    'email_address': getattr(credentials, 'email_address', None) if 'credentials' in locals() else None
                }
            }
    
    @staticmethod
    def verify_folder_access(access_token, email, folder="INBOX"):
        """
        Verifica el acceso a una carpeta específica en Gmail.
        
        Args:
            access_token (str): Token de acceso OAuth
            email (str): Dirección de correo
            folder (str): Carpeta a verificar
            
        Returns:
            dict: Resultado de la verificación
        """
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # Gmail API usa etiquetas en lugar de carpetas
            # Primero obtenemos las etiquetas disponibles
            labels_response = requests.get(
                f"https://gmail.googleapis.com/gmail/v1/users/{email}/labels",
                headers=headers
            )
            
            if labels_response.status_code != 200:
                return {
                    'success': False,
                    'message': f'Error al obtener etiquetas de Gmail: {labels_response.text}',
                    'has_read_permissions': False
                }
            
            # Gmail API permite consultar mensajes
            # Intentamos obtener un mensaje reciente (solo ID) para verificar permisos de lectura
            messages_response = requests.get(
                f"https://gmail.googleapis.com/gmail/v1/users/{email}/messages?maxResults=1",
                headers=headers
            )
            
            if messages_response.status_code != 200:
                return {
                    'success': False,
                    'message': f'Error al verificar permisos de lectura: {messages_response.text}',
                    'has_read_permissions': False
                }
            
            # Verificar si podemos acceder a la carpeta específica
            if folder == "INBOX":
                query_param = "label:inbox"
            elif folder.startswith("[Gmail]/"):
                gmail_label = folder.replace("[Gmail]/", "")
                query_param = f"label:{gmail_label}"
            else:
                query_param = f"label:{folder}"
            
            folder_response = requests.get(
                f"https://gmail.googleapis.com/gmail/v1/users/{email}/messages?maxResults=1&q={query_param}",
                headers=headers
            )
            
            if folder_response.status_code != 200:
                return {
                    'success': False,
                    'message': f'Error al acceder a la carpeta {folder}: {folder_response.text}',
                    'has_read_permissions': True
                }
            
            return {
                'success': True,
                'message': 'Acceso a carpeta verificado correctamente',
                'has_read_permissions': True
            }
            
        except Exception as e:
            logger.exception(f"Error al verificar acceso a carpeta: {str(e)}")
            return {
                'success': False,
                'message': f'Error al verificar acceso a carpeta: {str(e)}',
                'has_read_permissions': False
            }

    @staticmethod
    def update_service_status(tenant, credentials):
        try:
            # Obtener el servicio de ingesta
            servicio, created = ServicioIngesta.objects.get_or_create(tenant=tenant)
            
            # Verificar estado de las credenciales
            credentials_valid = credentials.authorized and credentials.is_token_valid()
            
            # Actualizar estado del servicio según las credenciales
            if not credentials_valid:
                if servicio.activo:
                    logger.info(f"Desactivando servicio de ingesta para tenant {tenant.id} por credenciales inválidas")
                    servicio.activo = False
                    servicio.save()
                    
                    # Registrar el evento en el log
                    LogActividad.objects.create(
                        tenant=tenant,
                        evento='SERVICIO_DETENIDO',
                        detalles="Servicio de ingesta detenido automáticamente por estado inválido de credenciales OAuth",
                    )
            else:
                # Si las credenciales son válidas pero el servicio está inactivo, activarlo
                if not servicio.activo:
                    logger.info(f"Activando servicio de ingesta para tenant {tenant.id} porque las credenciales son válidas")
                    servicio.activo = True
                    servicio.save()
                    
                    # Registrar el evento en el log
                    LogActividad.objects.create(
                        tenant=tenant,
                        evento='SERVICIO_INICIADO',
                        detalles="Servicio de ingesta activado automáticamente tras verificación exitosa de credenciales OAuth",
                    )
            
            # Actualizar última verificación
            servicio.ultima_verificacion = timezone.now()
            servicio.save()
            
        except Exception as e:
            logger.exception(f"Error al actualizar estado del servicio: {str(e)}")
            """
            Actualiza el estado del servicio de ingesta basado en el estado de OAuth.
            
            Args:
                tenant: El tenant a actualizar
                credentials: Las credenciales OAuth verificadas
            """
            try:
                # Obtener el servicio de ingesta
                servicio, created = ServicioIngesta.objects.get_or_create(tenant=tenant)
                
                # Si las credenciales no están autorizadas, desactivar el servicio
                if not credentials.authorized or not credentials.is_token_valid():
                    if servicio.activo:
                        logger.info(f"Desactivando servicio de ingesta para tenant {tenant.id} por credenciales inválidas")
                        servicio.activo = False
                        servicio.save()
                        
                        # Registrar el evento en el log
                        LogActividad.objects.create(
                            tenant=tenant,
                            evento='SERVICIO_DETENIDO',
                            detalles="Servicio de ingesta detenido automáticamente por estado inválido de credenciales OAuth",
                        )
                
                # Actualizar última verificación
                servicio.ultima_verificacion = timezone.now()
                servicio.save()
                
            except Exception as e:
                logger.exception(f"Error al actualizar estado del servicio: {str(e)}")