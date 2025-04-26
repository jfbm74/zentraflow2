import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.db import transaction
from django.db.models import Q

from apps.ingesta_correo.services.dashboard_service import DashboardService

from .models import ServicioIngesta, HistorialEjecucion, LogActividad, CorreoIngesta
from .services.ingesta_scheduler_service import IngestaSchedulerService
from apps.configuracion.models import EmailConfig
from .tasks import execute_ingestion_now

class DashboardIngestaView(LoginRequiredMixin, TemplateView):
    """Vista principal del dashboard de ingesta de correo."""
    template_name = 'ingesta_correo/dashboard.html'  # Esto ahora apunta a templates/ingesta_correo/dashboard.html
    login_url = '/auth/login/'
    
    def get_context_data(self, **kwargs):
        """Añadir datos de contexto para la plantilla."""
        context = super().get_context_data(**kwargs)
        tenant = self.request.user.tenant
        
        # Marcar como activo en el menú
        context['active_menu'] = 'ingesta_correo'
        
        # Obtener métricas de las últimas 24 horas
        context['metrics_24h'] = DashboardService.get_metrics_last_24h(tenant)
        
        # Obtener tendencias diarias
        daily_trends = DashboardService.get_daily_trends(tenant)
        context['daily_trends'] = daily_trends
        
        # Convertir tendencias a formato JSON para uso en JavaScript
        import json
        context['daily_trends_json'] = json.dumps(daily_trends)
        
        # Obtener estado del sistema
        context['system_status'] = DashboardService.get_system_status(tenant)
        
        # Obtener actividad reciente
        context['recent_activity'] = DashboardService.get_recent_activity(tenant)
        
        # Obtener correos recientes (los últimos 5)
        context['correos_recientes'] = CorreoIngesta.objects.filter(
            servicio__tenant=tenant
        ).order_by('-fecha_recepcion')[:5]
        
        return context

class ApiDashboardIngestaView(LoginRequiredMixin, View):
    """Vista API para obtener datos del dashboard."""
    
    def get(self, request):
        """Maneja solicitudes GET para obtener datos actualizados."""
        tenant = request.user.tenant
        
        data = {
            'metrics_24h': DashboardService.get_metrics_last_24h(tenant),
            'daily_trends': DashboardService.get_daily_trends(tenant),
            'system_status': DashboardService.get_system_status(tenant),
        }
        
        return JsonResponse(data)

class ToggleServicioView(LoginRequiredMixin, View):
    """Vista para activar/desactivar el servicio de ingesta."""
    
    def post(self, request):
        """Maneja solicitudes POST para cambiar el estado del servicio."""
        tenant = request.user.tenant
        
        try:
            # Verificar estado de la configuración de correo antes de activar el servicio
            try:
                config = EmailConfig.objects.get(tenant=tenant)
                email_config_valid = config.connection_status == 'conectado'
            except EmailConfig.DoesNotExist:
                email_config_valid = False
            
            servicio, created = ServicioIngesta.objects.get_or_create(tenant=tenant)
            
            # Si están intentando activar el servicio pero la configuración no es válida, no permitirlo
            new_state = not servicio.activo
            if new_state and not email_config_valid:
                return JsonResponse({
                    'success': False,
                    'message': "No se puede activar el servicio sin una configuración de correo válida."
                })
            
            servicio.activo = new_state
            servicio.modificado_por = request.user
            servicio.save()

            # Devolver respuesta exitosa
            return JsonResponse({
                'success': True,
                'message': f"Servicio {'activado' if new_state else 'desactivado'} correctamente",
                'active': new_state
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f"Error al cambiar estado del servicio: {str(e)}"
            }, status=500)

class CorreosListView(LoginRequiredMixin, TemplateView):
    """Vista para listar los correos procesados."""
    template_name = 'ingesta_correo/correos_list.html'
    login_url = '/auth/login/'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = self.request.user.tenant
        
        # Marcar como activo en el menú
        context['active_menu'] = 'ingesta_correo'
        context['active_submenu'] = 'correos'
        
        # Obtener parámetros de filtro
        estado = self.request.GET.get('estado', None)
        fecha_desde = self.request.GET.get('fecha_desde', None)
        fecha_hasta = self.request.GET.get('fecha_hasta', None)
        busqueda = self.request.GET.get('busqueda', None)
        
        # Obtener correos (con filtros si se han proporcionado)
        correos = CorreoIngesta.objects.filter(servicio__tenant=tenant)
        
        if estado:
            correos = correos.filter(estado=estado)
        
        if fecha_desde:
            try:
                from datetime import datetime
                fecha_obj = datetime.strptime(fecha_desde, '%Y-%m-%d')
                correos = correos.filter(fecha_recepcion__gte=fecha_obj)
            except Exception:
                pass
        
        if fecha_hasta:
            try:
                from datetime import datetime
                fecha_obj = datetime.strptime(fecha_hasta, '%Y-%m-%d')
                correos = correos.filter(fecha_recepcion__lte=fecha_obj)
            except Exception:
                pass
        
        if busqueda:
            correos = correos.filter(
                Q(asunto__icontains=busqueda) | 
                Q(remitente__icontains=busqueda) |
                Q(destinatarios__icontains=busqueda)
            )
        
        # Paginación
        from django.core.paginator import Paginator
        paginator = Paginator(correos.order_by('-fecha_recepcion'), 25)  # 25 correos por página
        page_number = self.request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        
        context['correos'] = page_obj
        context['filtros'] = {
            'estado': estado,
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta,
            'busqueda': busqueda
        }
        
        return context
    
class VerifyConnectionView(LoginRequiredMixin, View):
    """Vista para verificar la conexión al servidor de correo."""
    
    @method_decorator(csrf_protect)
    def post(self, request):
        """Maneja solicitudes POST para verificar la conexión."""
        tenant = request.user.tenant
        
        try:
            # Obtener configuración
            config = get_object_or_404(EmailConfig, tenant=tenant)
            
            # Probar conexión
            success, message = config.test_connection()
            
            return JsonResponse({
                'success': success,
                'message': message,
                'status': {
                    'connection_status': config.connection_status,
                    'last_check': config.last_check.isoformat() if config.last_check else None,
                    'email_address': config.email_address
                }
            })
            
        except EmailConfig.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'No hay configuración de correo establecida',
                'status': {
                    'connection_status': 'no_configurado',
                    'last_check': None,
                    'email_address': None
                }
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al verificar la conexión: {str(e)}',
                'status': {
                    'connection_status': 'error',
                    'last_check': None,
                    'email_address': None
                }
            }, status=500)

logger = logging.getLogger(__name__)

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