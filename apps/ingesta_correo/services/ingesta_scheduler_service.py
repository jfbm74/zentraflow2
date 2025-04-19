# apps/ingesta_correo/services/ingesta_scheduler_service.py

import logging
from django.utils import timezone
from django.db import transaction
from apps.ingesta_correo.models import ServicioIngesta, HistorialEjecucion, LogActividad
from apps.configuracion.services.oauth_verification_service import OAuthVerificationService

logger = logging.getLogger(__name__)

class IngestaSchedulerService:
    """
    Servicio para gestionar la programación y ejecución del servicio de ingesta de correo.
    """
    
    @staticmethod
    def inicializar_servicios():
        """
        Inicializa todos los servicios de ingesta activos, configurando sus tiempos de ejecución.
        """
        logger.info("Inicializando servicios de ingesta...")
        servicios = ServicioIngesta.objects.filter(activo=True)
        contador = 0
        
        for servicio in servicios:
            try:
                # Verificar que las credenciales OAuth son válidas
                oauth_status = OAuthVerificationService.verify_connection(servicio.tenant)
                
                if oauth_status['success']:
                    servicio.actualizar_proxima_ejecucion()
                    logger.info(f"Servicio inicializado para tenant {servicio.tenant.id}: próxima ejecución {servicio.proxima_ejecucion}")
                    contador += 1
                else:
                    logger.warning(f"No se pudo inicializar servicio para tenant {servicio.tenant.id}: {oauth_status['message']}")
                    # Registrar el problema
                    LogActividad.objects.create(
                        tenant=servicio.tenant,
                        evento='ERROR_INICIALIZACION',
                        detalles=f"No se pudo inicializar el servicio de ingesta: {oauth_status['message']}",
                        estado='ERROR'
                    )
            except Exception as e:
                logger.error(f"Error al inicializar servicio para tenant {servicio.tenant.id}: {str(e)}")
        
        logger.info(f"Se inicializaron {contador} servicios de ingesta")
        return contador
    
    @staticmethod
    def verificar_servicios_pendientes():
        """
        Verifica si hay algún servicio que deba ejecutarse ahora.
        """
        now = timezone.now()
        servicios_pendientes = ServicioIngesta.objects.filter(
            activo=True,
            en_ejecucion=False,
            proxima_ejecucion__lte=now
        )
        
        if servicios_pendientes.exists():
            logger.info(f"Se encontraron {servicios_pendientes.count()} servicios pendientes de ejecución")
        
        return servicios_pendientes
    
    @staticmethod
    def ejecutar_servicio(servicio_id):
        """
        Ejecuta el servicio de ingesta para un tenant específico.
        """
        try:
            with transaction.atomic():
                # Obtener servicio y bloquear para actualización
                servicio = ServicioIngesta.objects.select_for_update().get(id=servicio_id)
                
                # Verificar si ya está en ejecución
                if servicio.en_ejecucion:
                    logger.warning(f"El servicio {servicio_id} ya está en ejecución")
                    return False
                
                # Verificar si está activo
                if not servicio.activo:
                    logger.warning(f"El servicio {servicio_id} no está activo")
                    return False
                
                # Iniciar la ejecución
                servicio.iniciar_ejecucion()
                
                # Crear registro de historial
                historial = HistorialEjecucion.objects.create(
                    servicio=servicio,
                    tenant=servicio.tenant,
                    fecha_inicio=timezone.now(),
                    estado=HistorialEjecucion.EstadoEjecucion.EXITOSO
                )
                
                # Registrar en log de actividad
                LogActividad.objects.create(
                    tenant=servicio.tenant,
                    evento='INGESTA_INICIADA',
                    detalles=f"Ejecución del servicio de ingesta iniciada",
                    estado='INFO'
                )
                
                logger.info(f"Iniciada ejecución para servicio {servicio_id}")
                return {'servicio': servicio, 'historial': historial}
        
        except ServicioIngesta.DoesNotExist:
            logger.error(f"No se encontró el servicio con ID {servicio_id}")
            return False
        
        except Exception as e:
            logger.error(f"Error al iniciar ejecución del servicio {servicio_id}: {str(e)}")
            return False
    
    @staticmethod
    def finalizar_ejecucion(servicio_id, resultado):
        """
        Registra la finalización de una ejecución de servicio.
        
        Args:
            servicio_id: ID del servicio
            resultado: Dict con los resultados de la ejecución
                - estado: EXITOSO, ERROR, PARCIAL, CANCELADO
                - correos_procesados: número de correos procesados
                - correos_nuevos: número de correos nuevos encontrados
                - archivos_procesados: número de archivos procesados
                - glosas_extraidas: número de glosas extraídas
                - mensaje_error: mensaje de error (si aplica)
                - detalles: JSON con información adicional
        """
        try:
            with transaction.atomic():
                # Obtener servicio y bloquear para actualización
                servicio = ServicioIngesta.objects.select_for_update().get(id=servicio_id)
                
                # Si no está en ejecución, algo está mal
                if not servicio.en_ejecucion:
                    logger.warning(f"Intentando finalizar servicio {servicio_id} que no está en ejecución")
                
                # Registrar finalización en historial
                historial = HistorialEjecucion.objects.filter(
                    servicio=servicio,
                    fecha_fin__isnull=True
                ).order_by('-fecha_inicio').first()
                
                if historial:
                    # Actualizar historial
                    historial.fecha_fin = timezone.now()
                    historial.estado = resultado.get('estado', HistorialEjecucion.EstadoEjecucion.EXITOSO)
                    historial.correos_procesados = resultado.get('correos_procesados', 0)
                    historial.correos_nuevos = resultado.get('correos_nuevos', 0)
                    historial.archivos_procesados = resultado.get('archivos_procesados', 0)
                    historial.glosas_extraidas = resultado.get('glosas_extraidas', 0)
                    historial.mensaje_error = resultado.get('mensaje_error', None)
                    historial.detalles = resultado.get('detalles', None)
                    historial.calcular_duracion()
                    historial.save()
                    
                    # Registrar en log de actividad
                    evento = 'INGESTA_COMPLETADA' if historial.estado == HistorialEjecucion.EstadoEjecucion.EXITOSO else 'INGESTA_ERROR'
                    estado = 'SUCCESS' if historial.estado == HistorialEjecucion.EstadoEjecucion.EXITOSO else 'ERROR'
                    
                    LogActividad.objects.create(
                        tenant=servicio.tenant,
                        evento=evento,
                        detalles=f"Ejecución del servicio de ingesta finalizada: {historial.estado}. "
                                 f"Correos procesados: {historial.correos_procesados}, Glosas extraídas: {historial.glosas_extraidas}"
                                 + (f". Error: {historial.mensaje_error}" if historial.mensaje_error else ""),
                        estado=estado
                    )
                
                # Actualizar servicio
                servicio.registrar_ejecucion(resultado.get('correos_procesados', 0))
                
                logger.info(f"Finalizada ejecución para servicio {servicio_id}")
                return True
                
        except ServicioIngesta.DoesNotExist:
            logger.error(f"No se encontró el servicio con ID {servicio_id}")
            return False
        
        except Exception as e:
            logger.error(f"Error al finalizar ejecución del servicio {servicio_id}: {str(e)}")
            return False
    
    @staticmethod
    def cambiar_estado_servicio(servicio_id, activo, usuario=None):
        """
        Cambia el estado de un servicio de ingesta (activo/inactivo).
        
        Args:
            servicio_id: ID del servicio a modificar
            activo: Boolean indicando si debe estar activo o no
            usuario: Usuario que realiza el cambio
        
        Returns:
            dict: Resultado de la operación
        """
        try:
            servicio = ServicioIngesta.objects.get(id=servicio_id)
            
            # Si ya está en el estado solicitado, no hacer nada
            if servicio.activo == activo:
                return {
                    'success': True,
                    'message': f"El servicio ya estaba {'activo' if activo else 'inactivo'}",
                    'servicio_id': servicio.id,
                    'servicio_activo': servicio.activo,
                    'proxima_ejecucion': servicio.proxima_ejecucion.isoformat() if servicio.proxima_ejecucion else None
                }
            
            # Si se está activando, verificar que la configuración OAuth es válida
            if activo:
                oauth_status = OAuthVerificationService.verify_connection(servicio.tenant)
                
                if not oauth_status['success']:
                    return {
                        'success': False,
                        'message': f"No se puede activar el servicio: {oauth_status['message']}",
                        'servicio_id': servicio.id,
                        'servicio_activo': servicio.activo,
                        'proxima_ejecucion': servicio.proxima_ejecucion.isoformat() if servicio.proxima_ejecucion else None
                    }
            
            # Cambiar estado
            servicio.activo = activo
            
            # Si se está desactivando, limpiar estado de ejecución y próxima ejecución
            if not activo:
                servicio.en_ejecucion = False
                servicio.proxima_ejecucion = None
            # Si se está activando, actualizar próxima ejecución
            else:
                servicio.actualizar_proxima_ejecucion()
            
            # Registrar usuario que hizo el cambio
            if usuario:
                servicio.modificado_por = usuario
            
            servicio.save()
            
            # Registrar en log de actividad
            LogActividad.objects.create(
                tenant=servicio.tenant,
                evento='SERVICIO_INICIADO' if activo else 'SERVICIO_DETENIDO',
                detalles=f"Servicio de ingesta {'activado' if activo else 'desactivado'}" + 
                        (f" por usuario {usuario.email}" if usuario else ""),
                usuario=usuario
            )
            
            return {
                'success': True,
                'message': f"Servicio {'activado' if activo else 'desactivado'} correctamente",
                'servicio_id': servicio.id,
                'servicio_activo': servicio.activo,
                'proxima_ejecucion': servicio.proxima_ejecucion.isoformat() if servicio.proxima_ejecucion else None
            }
            
        except ServicioIngesta.DoesNotExist:
            return {
                'success': False,
                'message': f"No se encontró el servicio con ID {servicio_id}"
            }
        
        except Exception as e:
            logger.error(f"Error al cambiar estado del servicio {servicio_id}: {str(e)}")
            return {
                'success': False,
                'message': f"Error al cambiar el estado del servicio: {str(e)}"
            }
    
    @staticmethod
    def cambiar_intervalo(servicio_id, intervalo_minutos, usuario=None):
        """
        Cambia el intervalo de ejecución de un servicio.
        
        Args:
            servicio_id: ID del servicio a modificar
            intervalo_minutos: Nuevo intervalo en minutos
            usuario: Usuario que realiza el cambio
        
        Returns:
            dict: Resultado de la operación
        """
        try:
            # Validar intervalo
            intervalo_minutos = int(intervalo_minutos)
            if intervalo_minutos < 1:
                return {
                    'success': False,
                    'message': "El intervalo debe ser mayor a 0 minutos"
                }
            
            servicio = ServicioIngesta.objects.get(id=servicio_id)
            
            # Guardar intervalo anterior para el log
            intervalo_anterior = servicio.intervalo_minutos
            
            # Cambiar intervalo
            servicio.intervalo_minutos = intervalo_minutos
            
            # Recalcular próxima ejecución si está activo
            if servicio.activo:
                servicio.actualizar_proxima_ejecucion()
            
            # Registrar usuario que hizo el cambio
            if usuario:
                servicio.modificado_por = usuario
            
            servicio.save()
            
            # Registrar en log de actividad
            LogActividad.objects.create(
                tenant=servicio.tenant,
                evento='CONFIGURACION_ACTUALIZADA',
                detalles=f"Intervalo de ingesta cambiado de {intervalo_anterior} a {intervalo_minutos} minutos" + 
                        (f" por usuario {usuario.email}" if usuario else ""),
                usuario=usuario
            )
            
            return {
                'success': True,
                'message': f"Intervalo actualizado a {intervalo_minutos} minutos",
                'servicio': servicio
            }
            
        except ServicioIngesta.DoesNotExist:
            return {
                'success': False,
                'message': f"No se encontró el servicio con ID {servicio_id}"
            }
        
        except ValueError:
            return {
                'success': False,
                'message': "El intervalo debe ser un número entero"
            }
        
        except Exception as e:
            logger.error(f"Error al cambiar intervalo del servicio {servicio_id}: {str(e)}")
            return {
                'success': False,
                'message': f"Error al cambiar el intervalo del servicio: {str(e)}"
            }
    
    @staticmethod
    def ejecutar_ahora(servicio_id, usuario=None):
        """
        Fuerza la ejecución inmediata de un servicio.
        
        Args:
            servicio_id: ID del servicio a ejecutar
            usuario: Usuario que solicita la ejecución
        
        Returns:
            dict: Resultado de la operación
        """
        try:
            servicio = ServicioIngesta.objects.get(id=servicio_id)
            
            # Verificar si está activo
            if not servicio.activo:
                return {
                    'success': False,
                    'message': "No se puede ejecutar un servicio inactivo"
                }
            
            # Verificar si ya está en ejecución
            if servicio.en_ejecucion:
                return {
                    'success': False,
                    'message': "El servicio ya está en ejecución"
                }
            
            # Verificar OAuth antes de ejecutar
            oauth_status = OAuthVerificationService.verify_connection(servicio.tenant)
            if not oauth_status['success']:
                return {
                    'success': False,
                    'message': f"No se puede ejecutar el servicio: {oauth_status['message']}"
                }
            
            # Registrar en log la solicitud manual
            LogActividad.objects.create(
                tenant=servicio.tenant,
                evento='INGESTA_MANUAL_SOLICITADA',
                detalles=f"Ejecución manual del servicio de ingesta solicitada" + 
                        (f" por usuario {usuario.email}" if usuario else ""),
                usuario=usuario
            )
            
            # Programar para ejecución inmediata
            servicio.proxima_ejecucion = timezone.now()
            servicio.save(update_fields=['proxima_ejecucion'])
            
            # Devolver datos serializables, no el objeto servicio directamente
            return {
                'success': True,
                'message': "Servicio programado para ejecución inmediata",
                'servicio_id': servicio.id,
                'servicio_activo': servicio.activo,
                'proxima_ejecucion': servicio.proxima_ejecucion.isoformat() if servicio.proxima_ejecucion else None
            }
            
        except ServicioIngesta.DoesNotExist:
            return {
                'success': False,
                'message': f"No se encontró el servicio con ID {servicio_id}"
            }
        
        except Exception as e:
            logger.error(f"Error al ejecutar ahora el servicio {servicio_id}: {str(e)}")
            return {
                'success': False,
                'message': f"Error al ejecutar el servicio: {str(e)}"
            }