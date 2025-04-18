from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from .models import ServicioIngesta, ReglaFiltrado, CorreoIngesta, ArchivoAdjunto, LogActividad
from .services.dashboard_service import DashboardService
from apps.configuracion.services.oauth_verification_service import OAuthVerificationService



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
            # Verificar estado de OAuth antes de activar el servicio
            from apps.configuracion.models import EmailOAuthCredentials
            try:
                credentials = EmailOAuthCredentials.objects.get(tenant=tenant)
                oauth_valid = credentials.authorized and credentials.is_token_valid()
            except EmailOAuthCredentials.DoesNotExist:
                oauth_valid = False
            
            servicio, created = ServicioIngesta.objects.get_or_create(tenant=tenant)
            
            # Si están intentando activar el servicio pero OAuth no es válido, no permitirlo
            new_state = not servicio.activo
            if new_state and not oauth_valid:
                return JsonResponse({
                    'success': False,
                    'message': "No se puede activar el servicio sin una configuración OAuth válida."
                })
            
            servicio.activo = new_state
            servicio.modificado_por = request.user
            servicio.save()
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
                models.Q(asunto__icontains=busqueda) | 
                models.Q(remitente__icontains=busqueda) |
                models.Q(destinatarios__icontains=busqueda)
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
    """Vista para verificar la conexión OAuth con Gmail."""
    
    @method_decorator(csrf_protect)
    def post(self, request):
        """Maneja solicitudes POST para verificar la conexión."""
        tenant = request.user.tenant
        
        try:
            # Llamar al servicio de verificación
            result = OAuthVerificationService.verify_connection(tenant)
            return JsonResponse(result)
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al verificar la conexión: {str(e)}',
                'status': {
                    'oauth_authorized': False,
                    'oauth_token_valid': False,
                    'folder_accessible': False,
                    'read_permissions': False,
                    'email_address': None
                }
            }, status=500)