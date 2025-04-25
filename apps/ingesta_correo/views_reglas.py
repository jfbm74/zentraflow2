# apps/ingesta_correo/views_reglas.py
"""
Vistas para la gestión de reglas de filtrado.
"""

import logging
import json
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.forms import ValidationError
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.db import transaction

from apps.ingesta_correo.models import ReglaFiltrado, ServicioIngesta
from apps.ingesta_correo.services.regla_filtrado_service import ReglaFiltradoService

logger = logging.getLogger(__name__)

class ReglasFiltradoView(LoginRequiredMixin, TemplateView):
    """Vista para la página de gestión de reglas de filtrado."""
    template_name = 'ingesta_correo/reglas_list.html'
    login_url = '/auth/login/'
    
    def get_context_data(self, **kwargs):
        """Añadir datos de contexto para la plantilla."""
        context = super().get_context_data(**kwargs)
        tenant = self.request.user.tenant
        
        # Marcar menú como activo
        context['active_menu'] = 'ingesta_correo'
        context['active_submenu'] = 'reglas'
        
        # Obtener las reglas de filtrado para este tenant
        context['reglas'] = ReglaFiltradoService.get_reglas_for_tenant(tenant)
        
        # Obtener los campos, condiciones y acciones disponibles para reglas
        context['campos'] = ReglaFiltrado.TipoCampo.choices
        context['condiciones'] = ReglaFiltrado.TipoCondicion.choices
        context['acciones'] = ReglaFiltrado.TipoAccion.choices
        
        # Verificar si existe el servicio de ingesta
        servicio_existe = ServicioIngesta.objects.filter(tenant=tenant).exists()
        context['servicio_existe'] = servicio_existe
        
        return context

class ReglaFiltradoApiView(LoginRequiredMixin, View):
    """API para operaciones CRUD de reglas de filtrado."""
    
    @method_decorator(csrf_protect)
    def get(self, request, regla_id=None):
        """
        Obtiene detalles de una regla específica o lista todas las reglas.
        
        Args:
            request: Solicitud HTTP
            regla_id: ID opcional de la regla para obtener detalles
            
        Returns:
            JsonResponse con los datos solicitados
        """
        tenant = request.user.tenant
        
        try:
            if regla_id:
                # Obtener una regla específica
                try:
                    regla = ReglaFiltrado.objects.get(id=regla_id)
                    
                    # Verificar permisos
                    if regla.servicio.tenant != tenant and not request.user.is_superuser:
                        return JsonResponse({
                            'success': False,
                            'message': 'No tiene permisos para ver esta regla.'
                        }, status=403)
                    
                    # Devolver datos de la regla
                    return JsonResponse({
                        'success': True,
                        'regla': {
                            'id': regla.id,
                            'nombre': regla.nombre,
                            'campo': regla.campo,
                            'condicion': regla.condicion,
                            'valor': regla.valor,
                            'accion': regla.accion,
                            'activa': regla.activa,
                            'prioridad': regla.prioridad,
                            'creado_en': regla.creado_en.isoformat() if regla.creado_en else None,
                            'modificado_en': regla.modificado_en.isoformat() if regla.modificado_en else None,
                            'creado_por': regla.creado_por.email if regla.creado_por else None
                        }
                    })
                    
                except ReglaFiltrado.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'message': 'Regla no encontrada.'
                    }, status=404)
            else:
                # Obtener todas las reglas
                reglas = ReglaFiltradoService.get_reglas_for_tenant(tenant)
                
                # Formatear los datos para la respuesta
                reglas_data = [{
                    'id': regla.id,
                    'nombre': regla.nombre,
                    'campo': regla.campo,
                    'campo_display': regla.get_campo_display(),
                    'condicion': regla.condicion,
                    'condicion_display': regla.get_condicion_display(),
                    'valor': regla.valor,
                    'accion': regla.accion,
                    'accion_display': regla.get_accion_display(),
                    'activa': regla.activa,
                    'prioridad': regla.prioridad,
                } for regla in reglas]
                
                return JsonResponse({
                    'success': True,
                    'reglas': reglas_data
                })
                
        except Exception as e:
            logger.error(f"Error al obtener reglas: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f'Error al obtener reglas: {str(e)}'
            }, status=500)
    
    @method_decorator(csrf_protect)
    def post(self, request):
        """
        Crea una nueva regla de filtrado.
        
        Args:
            request: Solicitud HTTP con datos de la regla
            
        Returns:
            JsonResponse con el resultado de la operación
        """
        try:
            tenant = request.user.tenant
            usuario = request.user
            
            # Obtener datos del cuerpo de la solicitud
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                # Si no es JSON, intentar obtener de POST
                data = request.POST.dict()
            
            # Crear regla usando el servicio
            regla = ReglaFiltradoService.crear_regla(tenant, usuario, data)
            
            # Devolver respuesta exitosa
            return JsonResponse({
                'success': True,
                'message': 'Regla creada correctamente.',
                'regla': {
                    'id': regla.id,
                    'nombre': regla.nombre,
                    'campo': regla.campo,
                    'campo_display': regla.get_campo_display(),
                    'condicion': regla.condicion,
                    'condicion_display': regla.get_condicion_display(),
                    'valor': regla.valor,
                    'accion': regla.accion,
                    'accion_display': regla.get_accion_display(),
                    'activa': regla.activa,
                    'prioridad': regla.prioridad,
                }
            })
            
        except ValidationError as e:
            logger.warning(f"Error de validación al crear regla: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)
            
        except Exception as e:
            logger.error(f"Error al crear regla: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f'Error al crear la regla: {str(e)}'
            }, status=500)
    
    @method_decorator(csrf_protect)
    def put(self, request, regla_id):
        """
        Actualiza una regla de filtrado existente.
        
        Args:
            request: Solicitud HTTP con datos actualizados
            regla_id: ID de la regla a actualizar
            
        Returns:
            JsonResponse con el resultado de la operación
        """
        try:
            usuario = request.user
            
            # Obtener datos del cuerpo de la solicitud
            data = json.loads(request.body)
            
            # Actualizar regla usando el servicio
            regla = ReglaFiltradoService.actualizar_regla(regla_id, usuario, data)
            
            # Devolver respuesta exitosa
            return JsonResponse({
                'success': True,
                'message': 'Regla actualizada correctamente.',
                'regla': {
                    'id': regla.id,
                    'nombre': regla.nombre,
                    'campo': regla.campo,
                    'campo_display': regla.get_campo_display(),
                    'condicion': regla.condicion,
                    'condicion_display': regla.get_condicion_display(),
                    'valor': regla.valor,
                    'accion': regla.accion,
                    'accion_display': regla.get_accion_display(),
                    'activa': regla.activa,
                    'prioridad': regla.prioridad,
                }
            })
            
        except ValidationError as e:
            logger.warning(f"Error de validación al actualizar regla {regla_id}: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)
            
        except json.JSONDecodeError:
            logger.warning(f"Error al parsear JSON de la solicitud para actualizar regla {regla_id}")
            return JsonResponse({
                'success': False,
                'message': 'Formato de datos inválido. Se esperaba JSON.'
            }, status=400)
            
        except Exception as e:
            logger.error(f"Error al actualizar regla {regla_id}: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f'Error al actualizar la regla: {str(e)}'
            }, status=500)
    
    @method_decorator(csrf_protect)
    def delete(self, request, regla_id):
        """
        Elimina una regla de filtrado.
        
        Args:
            request: Solicitud HTTP
            regla_id: ID de la regla a eliminar
            
        Returns:
            JsonResponse con el resultado de la operación
        """
        try:
            usuario = request.user
            
            # Eliminar regla usando el servicio
            ReglaFiltradoService.eliminar_regla(regla_id, usuario)
            
            # Devolver respuesta exitosa
            return JsonResponse({
                'success': True,
                'message': 'Regla eliminada correctamente.'
            })
            
        except ValidationError as e:
            logger.warning(f"Error de validación al eliminar regla {regla_id}: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)
            
        except Exception as e:
            logger.error(f"Error al eliminar regla {regla_id}: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f'Error al eliminar la regla: {str(e)}'
            }, status=500)

class ReglaEstadoView(LoginRequiredMixin, View):
    """Vista para cambiar el estado (activo/inactivo) de una regla."""
    
    @method_decorator(csrf_protect)
    def post(self, request, regla_id):
        """
        Cambia el estado de una regla.
        
        Args:
            request: Solicitud HTTP con el nuevo estado
            regla_id: ID de la regla
            
        Returns:
            JsonResponse con el resultado de la operación
        """
        try:
            usuario = request.user
            
            # Obtener el estado del cuerpo de la solicitud
            try:
                data = json.loads(request.body)
                activa = data.get('activa', False)
            except json.JSONDecodeError:
                # Si no es JSON, intentar obtener de POST
                activa = request.POST.get('activa') == 'true'
            
            # Cambiar estado usando el servicio
            regla = ReglaFiltradoService.cambiar_estado_regla(regla_id, usuario, activa)
            
            # Devolver respuesta exitosa
            return JsonResponse({
                'success': True,
                'message': f'Estado de la regla {"activado" if activa else "desactivado"} correctamente.',
                'activa': regla.activa
            })
            
        except ValidationError as e:
            logger.warning(f"Error de validación al cambiar estado de regla {regla_id}: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)
            
        except Exception as e:
            logger.error(f"Error al cambiar estado de regla {regla_id}: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f'Error al cambiar estado de la regla: {str(e)}'
            }, status=500)

class ReglasReordenarView(LoginRequiredMixin, View):
    """Vista para reordenar las prioridades de las reglas."""
    
    @method_decorator(csrf_protect)
    def post(self, request):
        """
        Actualiza el orden de prioridad de las reglas.
        
        Args:
            request: Solicitud HTTP con el nuevo orden
            
        Returns:
            JsonResponse con el resultado de la operación
        """
        try:
            usuario = request.user
            
            # Obtener los datos de ordenamiento
            try:
                data = json.loads(request.body)
                orden_reglas = data.get('orden', [])
            except json.JSONDecodeError:
                return JsonResponse({
                    'success': False,
                    'message': 'Formato de datos inválido. Se esperaba JSON.'
                }, status=400)
            
            # Reordenar reglas usando el servicio
            ReglaFiltradoService.reordenar_reglas(usuario, orden_reglas)
            
            # Devolver respuesta exitosa
            return JsonResponse({
                'success': True,
                'message': 'Reglas reordenadas correctamente.'
            })
            
        except ValidationError as e:
            logger.warning(f"Error de validación al reordenar reglas: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)
            
        except Exception as e:
            logger.error(f"Error al reordenar reglas: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f'Error al reordenar reglas: {str(e)}'
            }, status=500)