# apps/ingesta_correo/services/ingesta_scheduler_service.py

import logging
from django.utils import timezone
from django.db import transaction
from apps.ingesta_correo.models import ServicioIngesta, HistorialEjecucion, LogActividad

logger = logging.getLogger(__name__)

class IngestaSchedulerService:
    """
    Servicio para gestionar la programación y ejecución del servicio de ingesta de correo.
    """
    
    @classmethod
    def inicializar_servicios(cls):
        """
        Inicializa todos los servicios de ingesta activos.
        Retorna el número de servicios inicializados.
        """
        count = 0
        try:
            servicios = ServicioIngesta.objects.filter(activo=True)
            for servicio in servicios:
                try:
                    # La verificación de correo ha sido simplificada
                    logger.info(f"Inicializando servicio de ingesta {servicio.id}")
                    count += 1
                except Exception as e:
                    logger.error(f"Error al inicializar servicio {servicio.id}: {str(e)}")
                    continue
            return count
        except Exception as e:
            logger.error(f"Error al inicializar servicios: {str(e)}")
            return 0
    
    @classmethod
    def verificar_servicios_pendientes(cls):
        """
        Verifica qué servicios están pendientes de ejecución según su programación.
        Retorna un QuerySet con los servicios que deben ejecutarse.
        """
        try:
            ahora = timezone.now()
            servicios = ServicioIngesta.objects.filter(
                activo=True,
                ultima_ejecucion__isnull=True
            ) | ServicioIngesta.objects.filter(
                activo=True,
                ultima_ejecucion__lt=ahora - timezone.timedelta(minutes=5)  # Intervalo mínimo entre ejecuciones
            )
            
            # En esta versión simplificada, todos los servicios son válidos
            return servicios
        except Exception as e:
            logger.error(f"Error al verificar servicios pendientes: {str(e)}")
            return ServicioIngesta.objects.none()
    
    @classmethod
    def ejecutar_servicio(cls, servicio_id):
        """
        Inicia la ejecución de un servicio de ingesta.
        Retorna un diccionario con el servicio y el historial creado.
        """
        try:
            with transaction.atomic():
                servicio = ServicioIngesta.objects.select_for_update().get(id=servicio_id)
                
                # Verificar si ya hay una ejecución en curso
                if HistorialEjecucion.objects.filter(
                    servicio=servicio,
                    estado=HistorialEjecucion.EstadoEjecucion.EN_PROCESO
                ).exists():
                    logger.warning(f"El servicio {servicio_id} ya tiene una ejecución en curso")
                    return None
                
                # Crear registro de historial
                historial = HistorialEjecucion.objects.create(
                    servicio=servicio,
                    estado=HistorialEjecucion.EstadoEjecucion.EN_PROCESO,
                    fecha_inicio=timezone.now()
                )
                
                # Actualizar servicio
                servicio.ultima_ejecucion = timezone.now()
                servicio.save()
                
                return {
                    'servicio': servicio,
                    'historial': historial
                }
        except Exception as e:
            logger.error(f"Error al ejecutar servicio {servicio_id}: {str(e)}")
            return None
    
    @classmethod
    def finalizar_ejecucion(cls, servicio_id, resultado):
        """
        Finaliza la ejecución de un servicio y registra los resultados.
        
        Args:
            servicio_id: ID del servicio
            resultado: Diccionario con los resultados de la ejecución
        """
        try:
            with transaction.atomic():
                servicio = ServicioIngesta.objects.select_for_update().get(id=servicio_id)
                historial = HistorialEjecucion.objects.filter(
                    servicio=servicio,
                    estado=HistorialEjecucion.EstadoEjecucion.EN_PROCESO
                ).latest('fecha_inicio')
                
                # Actualizar historial
                historial.estado = resultado.get('estado', HistorialEjecucion.EstadoEjecucion.ERROR)
                historial.fecha_fin = timezone.now()
                historial.correos_procesados = resultado.get('correos_procesados', 0)
                historial.correos_nuevos = resultado.get('correos_nuevos', 0)
                historial.archivos_procesados = resultado.get('archivos_procesados', 0)
                historial.glosas_extraidas = resultado.get('glosas_extraidas', 0)
                historial.mensaje_error = resultado.get('mensaje_error')
                historial.detalles = resultado.get('detalles', {})
                historial.save()
                
                # Actualizar servicio
                servicio.ultima_ejecucion = timezone.now()
                servicio.save()
                
                return True
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
                'servicio_id': servicio.id, 
                'intervalo_minutos': servicio.intervalo_minutos,
                'proxima_ejecucion': servicio.proxima_ejecucion.isoformat() if servicio.proxima_ejecucion else None
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