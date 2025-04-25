"""
Servicio para manejar la configuración de correo
"""
from ..models import EmailConfig
from apps.tenants.models import Tenant
from django.utils import timezone
from django.core.exceptions import ValidationError

class EmailConfigService:
    """Servicio para gestionar la configuración de correo por tenant."""
    
    @staticmethod
    def get_email_config(tenant):
        """
        Obtiene la configuración de correo para un tenant, o crea una nueva si no existe.
        
        Args:
            tenant: Instancia del modelo Tenant
            
        Returns:
            EmailConfig: Instancia de configuración de correo
        """
        config, created = EmailConfig.objects.get_or_create(tenant=tenant)
        return config
    
    @staticmethod
    def update_email_config(tenant, data, user=None):
        """
        Actualiza la configuración de correo para un tenant.
        
        Args:
            tenant: Instancia del modelo Tenant
            data: Diccionario con los datos a actualizar
            user: Usuario que realiza la actualización (opcional)
            
        Returns:
            dict: Resultado de la operación
        """
        try:
            # Obtener o crear la configuración
            config = EmailConfigService.get_email_config(tenant)
            
            # Actualizar campos
            if 'email_address' in data:
                config.email_address = data['email_address']
            
            if 'protocol' in data:
                config.protocol = data['protocol']
            
            if 'server_host' in data:
                config.server_host = data['server_host']
            
            if 'server_port' in data:
                config.server_port = int(data['server_port'])
            
            if 'username' in data:
                config.username = data['username']
            
            if 'password' in data and data['password']:
                config.password = data['password']
            
            if 'use_ssl' in data:
                config.use_ssl = data['use_ssl'] == 'true'
            
            if 'folder_to_monitor' in data:
                config.folder_to_monitor = data['folder_to_monitor']
            
            if 'check_interval' in data:
                config.check_interval = int(data['check_interval'])
            
            if 'mark_as_read' in data:
                config.mark_as_read = data['mark_as_read'] == 'true'
            
            if 'ingesta_enabled' in data:
                config.ingesta_enabled = data['ingesta_enabled'] == 'true'
            
            # Guardar cambios
            config.save()
            
            # Si se solicita actualizar el estado de conexión, probar la conexión
            if data.get('update_connection_status') == 'true':
                success, message = config.test_connection()
                # Recargamos la configuración para obtener el estado actual
                config.refresh_from_db()
                
                return {
                    'success': True,
                    'message': 'Configuración de correo actualizada correctamente.',
                    'config': config,
                    'connection_status': config.connection_status,
                    'connection_message': message
                }
            else:
                return {
                    'success': True,
                    'message': 'Configuración de correo actualizada correctamente.',
                    'config': config
                }
            
        except ValidationError as e:
            return {
                'success': False,
                'message': f'Error de validación: {str(e)}',
                'errors': e.messages
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error al actualizar la configuración: {str(e)}'
            }
    
    @staticmethod
    def test_connection(data):
        """
        Prueba la conexión con los datos proporcionados sin guardar la configuración.
        
        Args:
            data: Diccionario con los datos de conexión
            
        Returns:
            dict: Resultado de la prueba de conexión
        """
        try:
            protocol = data.get('protocol', 'imap')
            server_host = data.get('server_host', '')
            server_port = int(data.get('server_port', 0))
            username = data.get('username', '')
            password = data.get('password', '')
            use_ssl = data.get('use_ssl') == 'true'
            folder = data.get('folder_to_monitor', 'INBOX')
            
            # Validar datos mínimos
            if not server_host or not server_port or not username or not password:
                return {
                    'success': False,
                    'message': 'Faltan datos requeridos para la conexión.'
                }
            
            # Probar conexión según el protocolo
            if protocol == 'imap':
                import imaplib
                
                try:
                    if use_ssl:
                        server = imaplib.IMAP4_SSL(server_host, server_port)
                    else:
                        server = imaplib.IMAP4(server_host, server_port)
                    
                    server.login(username, password)
                    server.select(folder)
                    server.close()
                    server.logout()
                    
                    return {
                        'success': True,
                        'message': 'Conexión IMAP exitosa.'
                    }
                except imaplib.IMAP4.error as e:
                    return {
                        'success': False,
                        'message': f'Error de conexión IMAP: {str(e)}',
                        'error': str(e)
                    }
                
            elif protocol == 'pop3':
                import poplib
                
                try:
                    if use_ssl:
                        server = poplib.POP3_SSL(server_host, server_port)
                    else:
                        server = poplib.POP3(server_host, server_port)
                    
                    server.user(username)
                    server.pass_(password)
                    server.quit()
                    
                    return {
                        'success': True,
                        'message': 'Conexión POP3 exitosa.'
                    }
                except poplib.error_proto as e:
                    return {
                        'success': False,
                        'message': f'Error de conexión POP3: {str(e)}',
                        'error': str(e)
                    }
            else:
                return {
                    'success': False,
                    'message': f'Protocolo no soportado: {protocol}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Error inesperado al probar la conexión: {str(e)}',
                'error': str(e)
            } 