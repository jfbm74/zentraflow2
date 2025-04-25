# apps/ingesta_correo/views_ingesta.py

import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.db import transaction

from .models import ServicioIngesta, HistorialEjecucion, LogActividad
from .services.ingesta_scheduler_service import IngestaSchedulerService
from .tasks import execute_ingestion_now

logger = logging.getLogger(__name__)

class IngestaControlPanelView(LoginRequiredMixin, TemplateView):
    """Vista para el panel de control de la ingesta programada."""
    template_name = 'ingesta_correo/ingesta_control_panel.html'
    login_url = '/auth/login/'
    
    def get_context_data(self, **kwargs):
        """Añadir datos de contexto para la plantilla."""
        context = super().get_context_data(**kwargs)
        tenant = self.request.user.tenant
        
        # Marcar como activo en el menú
        context['active_menu'] = 'ingesta_correo'
        context['active_submenu'] = 'ingesta_programada'
        
        # Obtener el servicio de ingesta
        try:
            servicio = ServicioIngesta.objects.get(tenant=tenant)
            
            # Añadir información de tiempo restante
            tiempo_restante = servicio.tiempo_hasta_proxima_ejecucion()
            
            # Estado de conexión simplificado
            oauth_status = {'success': True, 'message': 'Conexión disponible'}
            
            context['servicio'] = servicio
            context['tiempo_restante'] = tiempo_restante
            context['oauth_status'] = oauth_status
            
            # Obtener historial reciente
            historial = HistorialEjecucion.objects.filter(tenant=tenant).order_by('-fecha_inicio')[:10]
            context['historial_ejecuciones'] = historial
            
            # Obtener actividad reciente
            actividad = LogActividad.objects.filter(
                tenant=tenant,
                evento__in=['INGESTA_INICIADA', 'INGESTA_COMPLETADA', 'INGESTA_ERROR', 
                           'INGESTA_MANUAL_SOLICITADA', 'SERVICIO_INICIADO', 'SERVICIO_DETENIDO']
            ).order_by('-fecha_hora')[:10]
            context['actividad_reciente'] = actividad
            
        except ServicioIngesta.DoesNotExist:
            # Si no existe, crear uno por defecto
            context['servicio'] = None
            context['tiempo_restante'] = "No programado"
            context['oauth_status'] = {'success': True, 'message': 'Conexión disponible'}
            context['historial_ejecuciones'] = []
            context['actividad_reciente'] = []
        
        return context


class ApiServicioIngestaView(LoginRequiredMixin, View):
    """API para gestionar el servicio de ingesta programada."""
    
    @method_decorator(csrf_protect)
    def get(self, request):
        """Obtener estado del servicio de ingesta."""
        tenant = request.user.tenant
        
        try:
            servicio = ServicioIngesta.objects.get(tenant=tenant)
            
            # Obtener historial reciente
            historial = HistorialEjecucion.objects.filter(tenant=tenant).order_by('-fecha_inicio')[:5]
            historial_data = []
            
            for h in historial:
                historial_data.append({
                    'id': h.id,
                    'fecha_inicio': h.fecha_inicio.isoformat() if h.fecha_inicio else None,
                    'fecha_fin': h.fecha_fin.isoformat() if h.fecha_fin else None,
                    'duracion_segundos': h.duracion_segundos,
                    'estado': h.estado,
                    'correos_procesados': h.correos_procesados,
                    'glosas_extraidas': h.glosas_extraidas,
                    'mensaje_error': h.mensaje_error
                })
            
            # Preparar respuesta
            return JsonResponse({
                'success': True,
                'servicio': {
                    'id': servicio.id,
                    'activo': servicio.activo,
                    'intervalo_minutos': servicio.intervalo_minutos,
                    'proxima_ejecucion': servicio.proxima_ejecucion.isoformat() if servicio.proxima_ejecucion else None,
                    'ultima_ejecucion': servicio.ultima_ejecucion.isoformat() if servicio.ultima_ejecucion else None,
                    'ultima_verificacion': servicio.ultima_verificacion.isoformat() if servicio.ultima_verificacion else None,
                    'en_ejecucion': servicio.en_ejecucion,
                    'tiempo_restante': servicio.tiempo_hasta_proxima_ejecucion(),
                    'correos_procesados_total': servicio.correos_procesados_total,
                    'correos_ultima_ejecucion': servicio.correos_ultima_ejecucion
                },
                'historial': historial_data
            })
        
        except ServicioIngesta.DoesNotExist:
            # Crear un servicio por defecto
            with transaction.atomic():
                servicio = ServicioIngesta.objects.create(
                    tenant=tenant,
                    activo=False,
                    intervalo_minutos=15
                )
                
                # Registrar en log de actividad
                LogActividad.objects.create(
                    tenant=tenant,
                    evento='SERVICIO_CREADO',
                    detalles="Servicio de ingesta creado automáticamente",
                    estado='INFO'
                )
            
            return JsonResponse({
                'success': True,
                'servicio': {
                    'id': servicio.id,
                    'activo': servicio.activo,
                    'intervalo_minutos': servicio.intervalo_minutos,
                    'proxima_ejecucion': None,
                    'ultima_ejecucion': None,
                    'ultima_verificacion': None,
                    'en_ejecucion': False,
                    'tiempo_restante': "No programado",
                    'correos_procesados_total': 0,
                    'correos_ultima_ejecucion': 0
                },
                'historial': []
            })
        
        except Exception as e:
            logger.error(f"Error al obtener estado del servicio: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f"Error al obtener estado del servicio: {str(e)}"
            }, status=500)
    
    @method_decorator(csrf_protect)
    def post(self, request):
        """Procesar acciones sobre el servicio de ingesta."""
        tenant = request.user.tenant
        action = request.POST.get('action')
        
        try:
            # Obtener servicio existente o crear uno nuevo
            servicio, created = ServicioIngesta.objects.get_or_create(
                tenant=tenant,
                defaults={
                    'activo': False,
                    'intervalo_minutos': 15
                }
            )
            
            # Procesar acción solicitada
            if action == 'toggle_service':
                # Cambiar estado del servicio (activo/inactivo)
                nuevo_estado = not servicio.activo
                result = IngestaSchedulerService.cambiar_estado_servicio(
                    servicio.id, 
                    nuevo_estado, 
                    request.user
                )
                return JsonResponse(result)
            
            elif action == 'execute_now':
                # Ejecutar inmediatamente
                result = IngestaSchedulerService.ejecutar_ahora(
                    servicio.id,
                    request.user
                )
                
                # Si fue exitoso, programar la tarea
                if result['success']:
                    execute_ingestion_now.delay(servicio.id, request.user.id)
                
                return JsonResponse(result)
            
            elif action == 'update_interval':
                # Cambiar intervalo de ejecución
                intervalo = request.POST.get('interval')
                if not intervalo:
                    return JsonResponse({
                        'success': False,
                        'message': "Debe proporcionar un intervalo válido"
                    })
                
                result = IngestaSchedulerService.cambiar_intervalo(
                    servicio.id,
                    intervalo,
                    request.user
                )
                return JsonResponse(result)
            
            else:
                return JsonResponse({
                    'success': False,
                    'message': f"Acción desconocida: {action}"
                })
        
        except Exception as e:
            logger.error(f"Error al procesar acción del servicio: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f"Error al procesar la solicitud: {str(e)}"
            }, status=500)


class HistorialIngestaView(LoginRequiredMixin, TemplateView):
    """Vista para mostrar el historial detallado de ejecuciones de ingesta."""
    template_name = 'ingesta_correo/historial_ingesta.html'
    login_url = '/auth/login/'
    
    def get_context_data(self, **kwargs):
        """Añadir datos de contexto para la plantilla."""
        context = super().get_context_data(**kwargs)
        tenant = self.request.user.tenant
        
        # Marcar como activo en el menú
        context['active_menu'] = 'ingesta_correo'
        context['active_submenu'] = 'historial_ingesta'
        
        # Obtener filtros
        estado = self.request.GET.get('estado')
        fecha_desde = self.request.GET.get('fecha_desde')
        fecha_hasta = self.request.GET.get('fecha_hasta')
        
        # Construir query
        historial = HistorialEjecucion.objects.filter(tenant=tenant)
        
        if estado:
            historial = historial.filter(estado=estado)
        
        if fecha_desde:
            try:
                from datetime import datetime
                fecha_obj = datetime.strptime(fecha_desde, '%Y-%m-%d')
                historial = historial.filter(fecha_inicio__gte=fecha_obj)
            except Exception:
                pass
        
        if fecha_hasta:
            try:
                from datetime import datetime
                fecha_obj = datetime.strptime(fecha_hasta, '%Y-%m-%d')
                historial = historial.filter(fecha_inicio__lte=fecha_obj)
            except Exception:
                pass
        
        # Paginación
        from django.core.paginator import Paginator
        paginator = Paginator(historial.order_by('-fecha_inicio'), 15)  # 15 items por página
        page_number = self.request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        
        context['historial'] = page_obj
        context['filtros'] = {
            'estado': estado,
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta
        }
        context['total_ejecuciones'] = historial.count()
        context['estados'] = HistorialEjecucion.EstadoEjecucion.choices
        
        return context


class ApiHistorialDetalleView(LoginRequiredMixin, View):
    """API para obtener detalles de una ejecución específica."""
    
    def get(self, request, historial_id):
        """Obtener detalles de una ejecución de ingesta."""
        tenant = request.user.tenant
        
        try:
            # Obtener el historial solicitado
            historial = get_object_or_404(HistorialEjecucion, id=historial_id, tenant=tenant)
            
            # Preparar datos detallados
            detalles = historial.detalles or {}
            
            # Obtener logs relacionados con esta ejecución
            logs = LogActividad.objects.filter(
                tenant=tenant,
                fecha_hora__range=(historial.fecha_inicio, historial.fecha_fin or timezone.now())
            ).order_by('fecha_hora')
            
            logs_data = []
            for log in logs:
                logs_data.append({
                    'fecha_hora': log.fecha_hora.isoformat(),
                    'evento': log.evento,
                    'detalles': log.detalles,
                    'estado': log.estado
                })
            
            # Retornar datos completos
            return JsonResponse({
                'success': True,
                'historial': {
                    'id': historial.id,
                    'fecha_inicio': historial.fecha_inicio.isoformat() if historial.fecha_inicio else None,
                    'fecha_fin': historial.fecha_fin.isoformat() if historial.fecha_fin else None,
                    'duracion_segundos': historial.duracion_segundos,
                    'estado': historial.estado,
                    'correos_procesados': historial.correos_procesados,
                    'correos_nuevos': historial.correos_nuevos,
                    'archivos_procesados': historial.archivos_procesados,
                    'glosas_extraidas': historial.glosas_extraidas,
                    'mensaje_error': historial.mensaje_error,
                    'detalles': detalles
                },
                'logs': logs_data
            })
        
        except Exception as e:
            logger.error(f"Error al obtener detalles del historial {historial_id}: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f"Error al obtener detalles: {str(e)}"
            }, status=500)