from celery import shared_task
from apps.configuracion.services.oauth_verification_service import OAuthVerificationService
from apps.tenants.models import Tenant
import logging
from django.utils import timezone
from apps.ingesta_correo.services.ingesta_scheduler_service import IngestaSchedulerService
from apps.ingesta_correo.models import ArchivoAdjunto, CorreoIngesta, ServicioIngesta, HistorialEjecucion, LogActividad


@shared_task
def sync_oauth_and_service_status():
    """Tarea programada para sincronizar el estado de OAuth y el servicio de ingesta."""
    for tenant in Tenant.objects.filter(is_active=True):
        # Verificar y actualizar el estado
        OAuthVerificationService.verify_connection(tenant)
    return "Sincronización OAuth completada"

logger = logging.getLogger(__name__)

@shared_task
def init_ingesta_services():
    """Tarea que se ejecuta al iniciar Celery para configurar todos los servicios de ingesta."""
    try:
        count = IngestaSchedulerService.inicializar_servicios()
        return f"Se inicializaron {count} servicios de ingesta"
    except Exception as e:
        logger.error(f"Error al inicializar servicios de ingesta: {str(e)}")
        return f"Error al inicializar servicios: {str(e)}"

@shared_task
def check_scheduled_services():
    """
    Tarea periódica que verifica si hay servicios de ingesta programados para ejecutarse.
    Esta tarea se ejecuta cada minuto.
    """
    try:
        # Buscar servicios pendientes de ejecución
        servicios_pendientes = IngestaSchedulerService.verificar_servicios_pendientes()
        
        # Si hay servicios pendientes, programar tareas para cada uno
        for servicio in servicios_pendientes:
            process_email_ingestion.delay(servicio.id)
        
        return f"Verificación completada: {servicios_pendientes.count()} servicios programados para ejecución"
    except Exception as e:
        logger.error(f"Error en la verificación de servicios programados: {str(e)}")
        return f"Error en la verificación: {str(e)}"


@shared_task
def process_email_ingestion(servicio_id):
    """
    Procesa la ingesta de correos para un servicio específico.
    
    Args:
        servicio_id: ID del servicio de ingesta a ejecutar
    """
    logger.info(f"Iniciando proceso de ingesta para servicio {servicio_id}")
    
    # Variables para estadísticas
    correos_procesados = 0
    correos_nuevos = 0
    archivos_procesados = 0
    glosas_extraidas = 0
    errores = []
    
    try:
        # Iniciar la ejecución y obtener el registro de historial
        result = IngestaSchedulerService.ejecutar_servicio(servicio_id)
        
        if not result:
            logger.error(f"No se pudo iniciar el servicio {servicio_id}")
            return f"Error: No se pudo iniciar el servicio {servicio_id}"
        
        servicio = result['servicio']
        historial = result['historial']
        
        # Verificar conexión OAuth antes de procesar
        oauth_status = OAuthVerificationService.verify_connection(servicio.tenant)
        
        if not oauth_status['success']:
            error_msg = f"Error de conexión OAuth: {oauth_status['message']}"
            logger.error(f"Error de conexión OAuth para servicio {servicio_id}: {oauth_status['message']}")
            
            # Registrar finalización con error
            IngestaSchedulerService.finalizar_ejecucion(servicio_id, {
                'estado': HistorialEjecucion.EstadoEjecucion.ERROR,
                'mensaje_error': error_msg,
                'correos_procesados': 0
            })
            
            return error_msg
        
        # Obtener credenciales OAuth y configurar cliente Gmail
        try:
            from apps.configuracion.models import EmailOAuthCredentials
            credentials = EmailOAuthCredentials.objects.get(tenant=servicio.tenant)
            
            from googleapiclient.discovery import build
            from google.oauth2.credentials import Credentials
            import base64
            import email
            from email.header import decode_header
            import os
            import tempfile
            
            # Construir credenciales OAuth2
            token_data = {
                'token': credentials.access_token,
                'refresh_token': credentials.refresh_token,
                'token_uri': 'https://oauth2.googleapis.com/token',
                'client_id': credentials.client_id,
                'client_secret': credentials.client_secret,
                'scopes': ['https://www.googleapis.com/auth/gmail.readonly']
            }
            
            creds = Credentials.from_authorized_user_info(token_data)
            gmail_service = build('gmail', 'v1', credentials=creds)
            
        except Exception as e:
            error_msg = f"Error al configurar cliente Gmail: {str(e)}"
            logger.error(f"Error al configurar cliente Gmail para servicio {servicio_id}: {str(e)}")
            errores.append(error_msg)
            raise
        
        # Obtener lista de mensajes no procesados
        try:
            response = gmail_service.users().messages().list(
                userId='me',
                q='in:inbox is:unread'
            ).execute()
            
            messages = response.get('messages', [])
            logger.info(f"Se encontraron {len(messages)} mensajes no leídos")
            
        except Exception as e:
            error_msg = f"Error al obtener lista de mensajes: {str(e)}"
            logger.error(f"Error al obtener mensajes para servicio {servicio_id}: {str(e)}")
            errores.append(error_msg)
            raise
        
        # Procesar cada mensaje
        for message in messages:
            try:
                msg_id = message['id']
                
                # Verificar si el mensaje ya fue procesado
                if CorreoIngesta.objects.filter(mensaje_id=msg_id).exists():
                    continue
                
                # Incrementar contador de correos nuevos
                correos_nuevos += 1
                
                # Obtener detalles del mensaje
                msg = gmail_service.users().messages().get(userId='me', id=msg_id, format='full').execute()
                
                # Procesar encabezados
                headers = {header['name']: header['value'] for header in msg['payload']['headers']}
                subject = headers.get('Subject', '')
                from_email = headers.get('From', '')
                to_email = headers.get('To', '')
                date = headers.get('Date', '')
                
                # Convertir fecha a datetime
                from dateutil import parser
                try:
                    received_date = parser.parse(date)
                except:
                    received_date = timezone.now()
                
                # Extraer contenido del correo
                plain_content = ""
                html_content = ""
                
                if 'parts' in msg['payload']:
                    for part in msg['payload']['parts']:
                        if part['mimeType'] == 'text/plain':
                            if 'data' in part['body']:
                                text = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                                plain_content = text
                        elif part['mimeType'] == 'text/html':
                            if 'data' in part['body']:
                                html = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                                html_content = html
                
                # Crear registro de correo
                correo = CorreoIngesta.objects.create(
                    servicio=servicio,
                    mensaje_id=msg_id,
                    remitente=from_email,
                    destinatarios=to_email,
                    asunto=subject,
                    fecha_recepcion=received_date,
                    contenido_plano=plain_content,
                    contenido_html=html_content,
                    estado=CorreoIngesta.Estado.PENDIENTE
                )
                
                # Incrementar contador de correos procesados
                correos_procesados += 1
                
                # Aplicar reglas de filtrado
                from apps.ingesta_correo.services.regla_filtrado_service import ReglaFiltradoService
                regla_aplicada = ReglaFiltradoService.aplicar_reglas(correo)
                
                # Si se debe ignorar según las reglas, marcar y continuar
                if regla_aplicada and regla_aplicada.accion == 'IGNORAR':
                    correo.estado = CorreoIngesta.Estado.IGNORADO
                    correo.regla_aplicada = regla_aplicada
                    correo.save()
                    continue
                
                # Procesar adjuntos
                if 'parts' in msg['payload']:
                    for part in msg['payload']['parts']:
                        if 'filename' in part and part['filename']:
                            try:
                                # Hay un adjunto
                                filename = part['filename']
                                
                                if 'body' in part and 'attachmentId' in part['body']:
                                    attachment_id = part['body']['attachmentId']
                                    attachment = gmail_service.users().messages().attachments().get(
                                        userId='me', messageId=msg_id, id=attachment_id
                                    ).execute()
                                    
                                    file_data = base64.urlsafe_b64decode(attachment['data'])
                                    mime_type = part.get('mimeType', 'application/octet-stream')
                                    
                                    # Guardar temporalmente el archivo
                                    temp_dir = tempfile.mkdtemp()
                                    temp_file_path = os.path.join(temp_dir, filename)
                                    
                                    with open(temp_file_path, 'wb') as f:
                                        f.write(file_data)
                                    
                                    # Crear registro de archivo adjunto
                                    from django.core.files.base import ContentFile
                                    adjunto = ArchivoAdjunto(
                                        correo=correo,
                                        nombre_archivo=filename,
                                        tipo_contenido=mime_type,
                                        tamaño=len(file_data)
                                    )
                                    
                                    # Guardar el archivo en el campo FileField
                                    with open(temp_file_path, 'rb') as f:
                                        adjunto.archivo.save(filename, ContentFile(f.read()))
                                    
                                    # Incrementar contador
                                    archivos_procesados += 1
                                    
                                    # Aquí procesarías el documento para extraer glosas
                                    # Por ahora, simulamos algunas glosas extraídas
                                    # Aquí implementarías la lógica de extracción de glosas
                                    import random
                                    num_glosas = random.randint(1, 5)  # Reemplazar con lógica real
                                    glosas_extraidas += num_glosas
                                    
                                    # Eliminar archivo temporal
                                    os.remove(temp_file_path)
                                    os.rmdir(temp_dir)
                            except Exception as e:
                                error_msg = f"Error al procesar adjunto {filename}: {str(e)}"
                                logger.error(f"Error al procesar adjunto para correo {msg_id}: {str(e)}")
                                errores.append(error_msg)
                                continue
                
                # Marcar correo como procesado
                correo.estado = CorreoIngesta.Estado.PROCESADO
                correo.fecha_procesamiento = timezone.now()
                correo.glosas_extraidas = num_glosas  # Actualizar con el número real de glosas
                correo.save()
                
                # Marcar como leído en Gmail
                try:
                    gmail_service.users().messages().modify(
                        userId='me',
                        id=msg_id,
                        body={'removeLabelIds': ['UNREAD']}
                    ).execute()
                except Exception as e:
                    error_msg = f"Error al marcar correo como leído: {str(e)}"
                    logger.warning(f"No se pudo marcar como leído el correo {msg_id}: {str(e)}")
                    errores.append(error_msg)
                
            except Exception as e:
                error_msg = f"Error al procesar correo {msg_id}: {str(e)}"
                logger.error(f"Error al procesar correo {msg_id} para servicio {servicio_id}: {str(e)}")
                errores.append(error_msg)
                continue
        
        # Determinar estado final
        estado_final = HistorialEjecucion.EstadoEjecucion.EXITOSO
        if len(errores) > 0:
            if correos_procesados > 0:
                estado_final = HistorialEjecucion.EstadoEjecucion.PARCIAL
            else:
                estado_final = HistorialEjecucion.EstadoEjecucion.ERROR
        
        # Registrar finalización
        IngestaSchedulerService.finalizar_ejecucion(servicio_id, {
            'estado': estado_final,
            'correos_procesados': correos_procesados,
            'correos_nuevos': correos_nuevos,
            'archivos_procesados': archivos_procesados,
            'glosas_extraidas': glosas_extraidas,
            'mensaje_error': '\n'.join(errores) if errores else None,
            'detalles': {
                'tiempo_conexion': 1,  # Actualizar con medición real
                'tiempo_procesamiento': 10,  # Actualizar con medición real
                'carpetas_revisadas': 1,
                'hora_inicio': timezone.now().isoformat(),
                'errores': errores,
                'total_mensajes_encontrados': len(messages) if 'messages' in locals() else 0
            }
        })
        
        logger.info(f"Proceso de ingesta completado para servicio {servicio_id}: {correos_procesados} correos procesados")
        return f"Ingesta completada: {correos_procesados} correos procesados, {glosas_extraidas} glosas extraídas"
        
    except Exception as e:
        error_msg = f"Error general en el proceso de ingesta: {str(e)}"
        logger.error(f"Error en el proceso de ingesta para servicio {servicio_id}: {str(e)}")
        
        # Registrar finalización con error
        IngestaSchedulerService.finalizar_ejecucion(servicio_id, {
            'estado': HistorialEjecucion.EstadoEjecucion.ERROR,
            'mensaje_error': error_msg,
            'correos_procesados': correos_procesados,
            'correos_nuevos': correos_nuevos,
            'archivos_procesados': archivos_procesados,
            'glosas_extraidas': glosas_extraidas,
            'detalles': {
                'errores': errores + [error_msg]
            }
        })
        
        return f"Error en la ingesta: {str(e)}"

@shared_task
def execute_ingestion_now(servicio_id, user_id=None):
    """
    Ejecuta inmediatamente un proceso de ingesta solicitado manualmente.
    
    Args:
        servicio_id: ID del servicio de ingesta
        user_id: ID del usuario que solicitó la ejecución (opcional)
    """
    logger.info(f"Ejecutando ingesta manual para servicio {servicio_id}")
    
    try:
        # Ejecutar normalmente, pero registrando que fue manual
        result = process_email_ingestion(servicio_id)
        logger.info(f"Ingesta manual completada para servicio {servicio_id}")
        return f"Ingesta manual completada: {result}"
    except Exception as e:
        logger.error(f"Error en ingesta manual para servicio {servicio_id}: {str(e)}")
        return f"Error en ingesta manual: {str(e)}"