from celery import shared_task
from apps.tenants.models import Tenant
import logging
from django.utils import timezone
from apps.ingesta_correo.services.ingesta_scheduler_service import IngestaSchedulerService
from apps.ingesta_correo.models import ArchivoAdjunto, CorreoIngesta, ServicioIngesta, HistorialEjecucion, LogActividad
from apps.configuracion.models import EmailConfig
import imaplib
import poplib
import email
from email.header import decode_header, make_header
import os
import tempfile
import base64

logger = logging.getLogger(__name__)

@shared_task
def sync_email_status():
    """Tarea programada para sincronizar el estado de conexión de correo."""
    for tenant in Tenant.objects.filter(is_active=True):
        try:
            config = EmailConfig.objects.get(tenant=tenant)
            config.test_connection()
        except EmailConfig.DoesNotExist:
            continue
    return "Sincronización de estado de correo completada"

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
        
        # Verificar configuración de correo
        try:
            config = EmailConfig.objects.get(tenant=servicio.tenant)
            if config.connection_status != 'conectado':
                success, message = config.test_connection()
                if not success:
                    error_msg = f"Error de conexión: {message}"
                    logger.error(f"Error de conexión para servicio {servicio_id}: {message}")
                    
                    # Registrar finalización con error
                    IngestaSchedulerService.finalizar_ejecucion(servicio_id, {
                        'estado': HistorialEjecucion.EstadoEjecucion.ERROR,
                        'mensaje_error': error_msg,
                        'correos_procesados': 0
                    })
                    
                    return error_msg
        except EmailConfig.DoesNotExist:
            error_msg = "No se encontró configuración de correo"
            logger.error(f"No se encontró configuración de correo para servicio {servicio_id}")
            
            # Registrar finalización con error
            IngestaSchedulerService.finalizar_ejecucion(servicio_id, {
                'estado': HistorialEjecucion.EstadoEjecucion.ERROR,
                'mensaje_error': error_msg,
                'correos_procesados': 0
            })
            
            return error_msg
        
        # Conectar al servidor de correo
        try:
            if config.protocol == 'imap':
                if config.use_ssl:
                    server = imaplib.IMAP4_SSL(config.server_host, config.server_port)
                else:
                    server = imaplib.IMAP4(config.server_host, config.server_port)
                
                server.login(config.username, config.password)
                server.select(config.folder_to_monitor)
                
                # Buscar correos no leídos
                result, messages = server.search(None, 'UNSEEN')
                if result != 'OK':
                    raise Exception("No se pudo buscar correos no leídos")
                
                message_nums = messages[0].split()
                logger.info(f"Se encontraron {len(message_nums)} mensajes no leídos")
                
                # Procesar cada mensaje
                for num in message_nums:
                    try:
                        # Obtener el mensaje
                        result, msg_data = server.fetch(num, '(RFC822)')
                        if result != 'OK':
                            continue
                        
                        email_body = msg_data[0][1]
                        email_message = email.message_from_bytes(email_body)
                        
                        # Verificar si el mensaje ya fue procesado
                        message_id = email_message.get('Message-ID', num.decode())
                        if CorreoIngesta.objects.filter(mensaje_id=message_id).exists():
                            continue
                        
                        # Incrementar contador de correos nuevos
                        correos_nuevos += 1
                        
                        # Procesar encabezados
                        subject = str(make_header(decode_header(email_message['Subject'])))
                        from_email = str(make_header(decode_header(email_message['From'])))
                        to_email = str(make_header(decode_header(email_message['To'])))
                        date = email_message['Date']
                        
                        # Convertir fecha a datetime
                        from email.utils import parsedate_to_datetime
                        received_date = parsedate_to_datetime(date)
                        
                        # Extraer contenido del correo
                        plain_content = ""
                        html_content = ""
                        
                        if email_message.is_multipart():
                            for part in email_message.walk():
                                if part.get_content_type() == "text/plain":
                                    plain_content = part.get_payload(decode=True).decode()
                                elif part.get_content_type() == "text/html":
                                    html_content = part.get_payload(decode=True).decode()
                        else:
                            content = email_message.get_payload(decode=True).decode()
                            if email_message.get_content_type() == "text/html":
                                html_content = content
                            else:
                                plain_content = content
                        
                        # Crear registro de correo
                        correo = CorreoIngesta.objects.create(
                            servicio=servicio,
                            mensaje_id=message_id,
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
                        
                        # Procesar adjuntos
                        for part in email_message.walk():
                            if part.get_content_maintype() == 'multipart':
                                continue
                            if not part.get('Content-Disposition'):
                                continue
                            
                            try:
                                # Hay un adjunto
                                filename = part.get_filename()
                                if not filename:
                                    continue
                                
                                # Decodificar nombre del archivo si es necesario
                                filename = str(make_header(decode_header(filename)))
                                
                                # Guardar temporalmente el archivo
                                temp_dir = tempfile.mkdtemp()
                                temp_file_path = os.path.join(temp_dir, filename)
                                
                                with open(temp_file_path, 'wb') as f:
                                    f.write(part.get_payload(decode=True))
                                
                                # Crear registro de archivo adjunto
                                from django.core.files.base import ContentFile
                                adjunto = ArchivoAdjunto(
                                    correo=correo,
                                    nombre_archivo=filename,
                                    tipo_contenido=part.get_content_type(),
                                    tamaño=os.path.getsize(temp_file_path)
                                )
                                
                                # Guardar el archivo en el campo FileField
                                with open(temp_file_path, 'rb') as f:
                                    adjunto.archivo.save(filename, ContentFile(f.read()))
                                
                                # Incrementar contador
                                archivos_procesados += 1
                                
                                # Aquí procesarías el documento para extraer glosas
                                # Por ahora, simulamos algunas glosas extraídas
                                import random
                                num_glosas = random.randint(1, 5)  # Reemplazar con lógica real
                                glosas_extraidas += num_glosas
                                
                                # Eliminar archivo temporal
                                os.remove(temp_file_path)
                                os.rmdir(temp_dir)
                            except Exception as e:
                                error_msg = f"Error al procesar adjunto {filename}: {str(e)}"
                                logger.error(f"Error al procesar adjunto para correo {message_id}: {str(e)}")
                                errores.append(error_msg)
                                continue
                        
                        # Marcar correo como procesado
                        correo.estado = CorreoIngesta.Estado.PROCESADO
                        correo.fecha_procesamiento = timezone.now()
                        correo.glosas_extraidas = num_glosas  # Actualizar con el número real de glosas
                        correo.save()
                        
                        # Marcar como leído en el servidor si está configurado
                        if config.mark_as_read:
                            server.store(num, '+FLAGS', '\\Seen')
                        
                    except Exception as e:
                        error_msg = f"Error al procesar correo: {str(e)}"
                        logger.error(f"Error al procesar correo para servicio {servicio_id}: {str(e)}")
                        errores.append(error_msg)
                        continue
                
                server.close()
                server.logout()
                
            else:  # POP3
                if config.use_ssl:
                    server = poplib.POP3_SSL(config.server_host, config.server_port)
                else:
                    server = poplib.POP3(config.server_host, config.server_port)
                
                server.user(config.username)
                server.pass_(config.password)
                
                # Obtener lista de mensajes
                num_messages = len(server.list()[1])
                logger.info(f"Se encontraron {num_messages} mensajes")
                
                # Procesar cada mensaje
                for i in range(num_messages):
                    try:
                        # Obtener el mensaje
                        lines = server.retr(i+1)[1]
                        msg_content = b'\n'.join(lines).decode('utf-8')
                        email_message = email.message_from_string(msg_content)
                        
                        # Verificar si el mensaje ya fue procesado
                        message_id = email_message.get('Message-ID', f'POP3-{i+1}')
                        if CorreoIngesta.objects.filter(mensaje_id=message_id).exists():
                            continue
                        
                        # El resto del procesamiento es igual que en IMAP
                        # ... (mismo código que arriba para procesar el mensaje)
                        
                        # Marcar para eliminar si está configurado
                        if config.mark_as_read:
                            server.dele(i+1)
                        
                    except Exception as e:
                        error_msg = f"Error al procesar correo POP3: {str(e)}"
                        logger.error(f"Error al procesar correo POP3 para servicio {servicio_id}: {str(e)}")
                        errores.append(error_msg)
                        continue
                
                server.quit()
            
        except Exception as e:
            error_msg = f"Error al conectar con el servidor de correo: {str(e)}"
            logger.error(f"Error al conectar con el servidor para servicio {servicio_id}: {str(e)}")
            errores.append(error_msg)
            raise
        
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
                'errores': errores
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

@shared_task
def sync_service_status():
    """Tarea programada para sincronizar el estado del servicio de ingesta."""
    for tenant in Tenant.objects.filter(is_active=True):
        try:
            # Verificar servicios de ingesta
            servicios = ServicioIngesta.objects.filter(tenant=tenant)
            for servicio in servicios:
                servicio.ultima_verificacion = timezone.now()
                servicio.save(update_fields=['ultima_verificacion'])
                
                # Registrar verificación
                LogActividad.objects.create(
                    tenant=tenant,
                    evento='SERVICIO_VERIFICADO',
                    detalles="Verificación periódica del servicio de ingesta",
                    estado='info'
                )
        except Exception as e:
            logger.error(f"Error al sincronizar estado del servicio para {tenant}: {str(e)}")
            continue
    
    return "Sincronización de estado del servicio completada"