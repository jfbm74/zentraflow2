# apps/ingesta_correo/services/regla_filtrado_service.py
"""
Servicio para la gestión de reglas de filtrado.
Implementa la lógica de negocio para crear, actualizar, eliminar y listar reglas.
"""

import logging
from django.db import transaction
from django.utils import timezone
from django.forms import ValidationError
from apps.ingesta_correo.models import ReglaFiltrado, ServicioIngesta, LogActividad
from apps.ingesta_correo.services.regla_test_service import ReglaTestService

logger = logging.getLogger(__name__)

class ReglaFiltradoService:
    """Servicio para gestionar reglas de filtrado de correos."""
    
    @staticmethod
    def get_reglas_for_tenant(tenant, activas_only=False):
        """Obtiene las reglas de filtrado para un tenant específico."""
        try:
            # Obtener el servicio de ingesta asociado al tenant
            servicio = ServicioIngesta.objects.get(tenant=tenant)
            
            # Filtrar las reglas por servicio y estado si se requiere
            query = ReglaFiltrado.objects.filter(servicio=servicio)
            if activas_only:
                query = query.filter(activa=True)
            
            # Ordenar por prioridad y fecha de creación
            return query.order_by('prioridad', 'creado_en')
            
        except ServicioIngesta.DoesNotExist:
            logger.warning(f"No existe servicio de ingesta para el tenant {tenant.id}")
            return ReglaFiltrado.objects.none()
        
        except Exception as e:
            logger.error(f"Error al obtener reglas para tenant {tenant.id}: {str(e)}")
            return ReglaFiltrado.objects.none()
    
    @staticmethod
    def crear_regla(tenant, usuario, data):
        """
        Crea una nueva regla de filtrado para un tenant.
        
        Args:
            tenant: El tenant para el que se crea la regla
            usuario: El usuario que crea la regla
            data: Diccionario con los datos de la regla
            
        Returns:
            ReglaFiltrado: La regla creada
            
        Raises:
            ValidationError: Si los datos no son válidos
        """
        try:
            with transaction.atomic():
                # Validar datos
                nombre = data.get('nombre', '').strip()
                campo = data.get('campo', '')
                condicion = data.get('condicion', '')
                valor = data.get('valor', '').strip()
                accion = data.get('accion', '')
                prioridad = data.get('prioridad', 0)
                activa = data.get('activa', True)
                
                # Validaciones
                if not nombre:
                    raise ValidationError('El nombre de la regla es obligatorio.')
                if not campo:
                    raise ValidationError('El campo a evaluar es obligatorio.')
                if not condicion:
                    raise ValidationError('La condición es obligatoria.')
                if not valor:
                    raise ValidationError('El valor de la condición es obligatorio.')
                if not accion:
                    raise ValidationError('La acción a realizar es obligatoria.')
                
                # Obtener o crear servicio de ingesta
                servicio, _ = ServicioIngesta.objects.get_or_create(tenant=tenant)
                
                # Crear regla
                regla = ReglaFiltrado.objects.create(
                    servicio=servicio,
                    nombre=nombre,
                    campo=campo,
                    condicion=condicion,
                    valor=valor,
                    accion=accion,
                    prioridad=int(prioridad),
                    activa=activa,
                    creado_por=usuario
                )
                
                # Registrar en log de actividad
                LogActividad.objects.create(
                    tenant=tenant,
                    evento='REGLA_CREADA',
                    detalles=f"Regla '{nombre}' creada por {usuario.email}",
                    usuario=usuario
                )
                
                logger.info(f"Regla creada: tenant={tenant.id}, nombre='{nombre}', usuario={usuario.email}")
                return regla
                
        except ValidationError as e:
            logger.warning(f"Error de validación al crear regla: {str(e)}")
            raise
        
        except Exception as e:
            logger.error(f"Error al crear regla: {str(e)}")
            raise ValidationError(f"Error al crear la regla: {str(e)}")
    
    @staticmethod
    def actualizar_regla(regla_id, usuario, data):
        """
        Actualiza una regla de filtrado existente.
        
        Args:
            regla_id: ID de la regla a actualizar
            usuario: Usuario que realiza la actualización
            data: Diccionario con los datos actualizados
            
        Returns:
            ReglaFiltrado: La regla actualizada
            
        Raises:
            ValidationError: Si los datos no son válidos o la regla no existe
        """
        try:
            with transaction.atomic():
                # Obtener la regla
                try:
                    regla = ReglaFiltrado.objects.get(id=regla_id)
                except ReglaFiltrado.DoesNotExist:
                    raise ValidationError('La regla no existe.')
                
                # Verificar que el usuario pertenece al mismo tenant que la regla
                if usuario.tenant != regla.servicio.tenant and not usuario.is_superuser:
                    raise ValidationError('No tiene permisos para editar esta regla.')
                
                # Actualizar campos
                if 'nombre' in data:
                    nombre = data['nombre'].strip()
                    if not nombre:
                        raise ValidationError('El nombre de la regla es obligatorio.')
                    regla.nombre = nombre
                
                if 'campo' in data:
                    campo = data['campo']
                    if not campo:
                        raise ValidationError('El campo a evaluar es obligatorio.')
                    regla.campo = campo
                
                if 'condicion' in data:
                    condicion = data['condicion']
                    if not condicion:
                        raise ValidationError('La condición es obligatoria.')
                    regla.condicion = condicion
                
                if 'valor' in data:
                    valor = data['valor'].strip()
                    if not valor:
                        raise ValidationError('El valor de la condición es obligatorio.')
                    regla.valor = valor
                
                if 'accion' in data:
                    accion = data['accion']
                    if not accion:
                        raise ValidationError('La acción a realizar es obligatoria.')
                    regla.accion = accion
                
                if 'prioridad' in data:
                    regla.prioridad = int(data['prioridad'])
                
                if 'activa' in data:
                    regla.activa = data['activa']
                
                # Guardar cambios
                regla.save()
                
                # Registrar en log de actividad
                LogActividad.objects.create(
                    tenant=regla.servicio.tenant,
                    evento='REGLA_MODIFICADA',
                    detalles=f"Regla '{regla.nombre}' modificada por {usuario.email}",
                    usuario=usuario
                )
                
                logger.info(f"Regla actualizada: id={regla_id}, nombre='{regla.nombre}', usuario={usuario.email}")
                return regla
                
        except ValidationError as e:
            logger.warning(f"Error de validación al actualizar regla {regla_id}: {str(e)}")
            raise
        
        except Exception as e:
            logger.error(f"Error al actualizar regla {regla_id}: {str(e)}")
            raise ValidationError(f"Error al actualizar la regla: {str(e)}")
    
    @staticmethod
    def eliminar_regla(regla_id, usuario):
        """
        Elimina una regla de filtrado.
        
        Args:
            regla_id: ID de la regla a eliminar
            usuario: Usuario que realiza la eliminación
            
        Returns:
            bool: True si la eliminación fue exitosa
            
        Raises:
            ValidationError: Si la regla no existe o el usuario no tiene permisos
        """
        try:
            # Obtener la regla
            try:
                regla = ReglaFiltrado.objects.get(id=regla_id)
            except ReglaFiltrado.DoesNotExist:
                raise ValidationError('La regla no existe.')
            
            # Verificar que el usuario pertenece al mismo tenant que la regla
            if usuario.tenant != regla.servicio.tenant and not usuario.is_superuser:
                raise ValidationError('No tiene permisos para eliminar esta regla.')
            
            # Guardar información para el log antes de eliminar
            tenant = regla.servicio.tenant
            nombre_regla = regla.nombre
            
            # Eliminar regla
            regla.delete()
            
            # Registrar en log de actividad
            LogActividad.objects.create(
                tenant=tenant,
                evento='REGLA_ELIMINADA',
                detalles=f"Regla '{nombre_regla}' eliminada por {usuario.email}",
                usuario=usuario
            )
            
            logger.info(f"Regla eliminada: id={regla_id}, nombre='{nombre_regla}', usuario={usuario.email}")
            return True
            
        except ValidationError as e:
            logger.warning(f"Error de validación al eliminar regla {regla_id}: {str(e)}")
            raise
        
        except Exception as e:
            logger.error(f"Error al eliminar regla {regla_id}: {str(e)}")
            raise ValidationError(f"Error al eliminar la regla: {str(e)}")
    
    @staticmethod
    def cambiar_estado_regla(regla_id, usuario, activa):
        """
        Cambia el estado (activa/inactiva) de una regla.
        
        Args:
            regla_id: ID de la regla
            usuario: Usuario que realiza el cambio
            activa: Nuevo estado (True/False)
            
        Returns:
            ReglaFiltrado: La regla actualizada
            
        Raises:
            ValidationError: Si la regla no existe o el usuario no tiene permisos
        """
        try:
            # Obtener la regla
            try:
                regla = ReglaFiltrado.objects.get(id=regla_id)
            except ReglaFiltrado.DoesNotExist:
                raise ValidationError('La regla no existe.')
            
            # Verificar que el usuario pertenece al mismo tenant que la regla
            if usuario.tenant != regla.servicio.tenant and not usuario.is_superuser:
                raise ValidationError('No tiene permisos para modificar esta regla.')
            
            # Actualizar estado si ha cambiado
            if regla.activa != activa:
                regla.activa = activa
                regla.save()
                
                # Registrar en log de actividad
                estado = "activada" if activa else "desactivada"
                LogActividad.objects.create(
                    tenant=regla.servicio.tenant,
                    evento='REGLA_MODIFICADA',
                    detalles=f"Regla '{regla.nombre}' {estado} por {usuario.email}",
                    usuario=usuario
                )
                
                logger.info(f"Regla {estado}: id={regla_id}, nombre='{regla.nombre}', usuario={usuario.email}")
            
            return regla
            
        except ValidationError as e:
            logger.warning(f"Error de validación al cambiar estado de regla {regla_id}: {str(e)}")
            raise
        
        except Exception as e:
            logger.error(f"Error al cambiar estado de regla {regla_id}: {str(e)}")
            raise ValidationError(f"Error al cambiar el estado de la regla: {str(e)}")
    
    @staticmethod
    def reordenar_reglas(usuario, orden_reglas):
        """
        Actualiza el orden de prioridad de las reglas.
        
        Args:
            usuario: Usuario que realiza el reordenamiento
            orden_reglas: Lista de diccionarios con {id: regla_id, prioridad: nueva_prioridad}
            
        Returns:
            bool: True si la actualización fue exitosa
            
        Raises:
            ValidationError: Si hay problemas con el reordenamiento
        """
        try:
            with transaction.atomic():
                # Verificar que hay reglas para reordenar
                if not orden_reglas:
                    return True
                
                tenant = usuario.tenant
                
                # Procesar cada regla en el nuevo orden
                for item in orden_reglas:
                    regla_id = item.get('id')
                    prioridad = item.get('prioridad')
                    
                    if not regla_id or prioridad is None:
                        continue
                    
                    try:
                        regla = ReglaFiltrado.objects.get(id=regla_id)
                        
                        # Verificar que el usuario tiene permisos para esta regla
                        if regla.servicio.tenant != tenant and not usuario.is_superuser:
                            logger.warning(f"Usuario {usuario.email} intentó reordenar regla {regla_id} de otro tenant")
                            continue
                        
                        # Actualizar prioridad si ha cambiado
                        if regla.prioridad != prioridad:
                            regla.prioridad = prioridad
                            regla.save(update_fields=['prioridad'])
                    
                    except ReglaFiltrado.DoesNotExist:
                        logger.warning(f"Regla {regla_id} no existe al intentar reordenar")
                
                # Registrar en log de actividad
                LogActividad.objects.create(
                    tenant=tenant,
                    evento='REGLA_MODIFICADA',
                    detalles=f"Prioridades de reglas reordenadas por {usuario.email}",
                    usuario=usuario
                )
                
                logger.info(f"Reglas reordenadas por usuario {usuario.email}")
                return True
                
        except Exception as e:
            logger.error(f"Error al reordenar reglas: {str(e)}")
            raise ValidationError(f"Error al reordenar las reglas: {str(e)}")
    
    @staticmethod
    def aplicar_reglas(correo):
        """
        Aplica las reglas de filtrado a un correo.
        
        Args:
            correo: Objeto CorreoIngesta a evaluar
            
        Returns:
            ReglaFiltrado: La primera regla que coincide con el correo, o None si ninguna coincide
        """
        try:
            # Obtener reglas activas ordenadas por prioridad
            reglas = ReglaFiltrado.objects.filter(
                servicio=correo.servicio,
                activa=True
            ).order_by('prioridad')
            
            # Preparar datos para evaluación
            datos_correo = {
                'asunto': correo.asunto or '',
                'remitente': correo.remitente or '',
                'destinatario': correo.destinatarios or '',
                'contenido': correo.contenido_plano or '',
                'adjunto': ', '.join([adj.nombre_archivo for adj in correo.adjuntos.all()]) if correo.adjuntos.exists() else ''
            }
            
            # Evaluar cada regla en orden
            for regla in reglas:
                resultado = ReglaTestService.evaluar_regla_completa(regla, datos_correo)
                
                if resultado['cumple']:
                    logger.info(f"Regla '{regla.nombre}' coincide con correo {correo.id}: {resultado['mensaje']}")
                    return regla
            
            return None
            
        except Exception as e:
            logger.error(f"Error al aplicar reglas a correo {correo.id}: {str(e)}")
            return None