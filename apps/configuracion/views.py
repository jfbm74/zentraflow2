import json
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from tenants.models import Tenant
from .models import ConfiguracionTenant, ReglaFiltracionCorreo, RangoIP, HistorialSincronizacion
from .services import ConfiguracionService
from .forms import ConfiguracionGeneralForm, ConfiguracionCorreoForm, ConfiguracionSeguridadForm

class ConfiguracionView(LoginRequiredMixin, TemplateView):
    """Vista para la configuración del cliente (tenant)."""
    template_name = "configuracion/configuracion.html"
    login_url = '/auth/login/'
    
    def get_context_data(self, **kwargs):
        """Añadir datos de contexto para la plantilla."""
        context = super().get_context_data(**kwargs)
        context['active_menu'] = 'configuracion'  # Para marcar como activo el ítem del menú
        
        # Determinar el tenant a mostrar
        tenant_id = self.kwargs.get('tenant_id')
        if tenant_id and (self.request.user.is_superuser or self.request.user.role == 'ADMIN'):
            tenant = get_object_or_404(Tenant, id=tenant_id)
        else:
            tenant = self.request.user.tenant
            
        # Obtener configuración
        configuracion = ConfiguracionService.get_configuracion(tenant)
        
        context['current_tenant'] = tenant
        context['configuracion'] = configuracion
        
        # Obtener reglas de filtro y rangos IP
        context['reglas_filtro'] = configuracion.reglas_filtro.all()
        context['rangos_ip'] = configuracion.rangos_ip.all()
        
        # Obtener historial de sincronización
        context['historial_sincronizacion'] = ConfiguracionService.obtener_historial_sincronizacion(configuracion)
        
        # Para Super Admin, cargar todos los tenants
        if self.request.user.is_superuser or self.request.user.role == 'ADMIN':
            context['tenants'] = Tenant.objects.filter(is_active=True).order_by('name')
            context['is_super_admin'] = self.request.user.is_superuser
            context['is_editable'] = True
        else:
            context['is_editable'] = False
            
        # Fecha y usuario de última actualización
        context['ultima_actualizacion'] = configuracion.ultima_actualizacion if configuracion.ultima_actualizacion else timezone.now()
        context['actualizado_por'] = configuracion.actualizado_por.full_name if configuracion.actualizado_por else self.request.user.full_name
            
        return context
    
    def post(self, request, *args, **kwargs):
        """Procesar formulario de configuración."""
        # Determinar el tenant a actualizar
        tenant_id = self.kwargs.get('tenant_id')
        if tenant_id and (request.user.is_superuser or request.user.role == 'ADMIN'):
            tenant = get_object_or_404(Tenant, id=tenant_id)
        else:
            tenant = request.user.tenant
        
        # Determinar qué pestaña se está actualizando
        tab = request.POST.get('tab', 'general')
        
        if tab == 'general':
            # Procesar formulario general
            form_data = {
                'zona_horaria': request.POST.get('zona_horaria'),
                'formato_fecha': request.POST.get('formato_fecha'),
                'idioma': request.POST.get('idioma'),
                'modulo_ingesta': request.POST.get('modulo_ingesta') == 'true',
                'modulo_extraccion': request.POST.get('modulo_extraccion') == 'true',
                'modulo_flujo': request.POST.get('modulo_flujo') == 'true',
                'modulo_pdf': request.POST.get('modulo_pdf') == 'true',
                'clientName': request.POST.get('clientName'),
                'clientNIT': request.POST.get('clientNIT'),
            }
            
            # Procesar logo si se adjuntó
            if 'logo' in request.FILES:
                form_data['logo'] = request.FILES['logo']
                
            # Verificar si se debe eliminar el logo
            if request.POST.get('eliminar_logo') == 'true':
                form_data['eliminar_logo'] = True
                
            ConfiguracionService.guardar_configuracion_general(tenant, form_data, request.user)
            return JsonResponse({'success': True, 'message': 'Configuración general guardada con éxito'})
            
        elif tab == 'correo':
            # Procesar formulario de correo
            form_data = {
                'ingesta_habilitada': request.POST.get('ingesta_habilitada') == 'true',
                'correo_monitoreo': request.POST.get('correo_monitoreo'),
                'metodo_autenticacion': request.POST.get('metodo_autenticacion'),
                'client_id': request.POST.get('client_id'),
                'client_secret': request.POST.get('client_secret'),
                'carpeta_monitoreo': request.POST.get('carpeta_monitoreo'),
                'intervalo_verificacion': int(request.POST.get('intervalo_verificacion', 5)),
                'marcar_leidos': request.POST.get('marcar_leidos') == 'true',
            }
            
            configuracion = ConfiguracionService.guardar_configuracion_correo(tenant, form_data, request.user)
                
            # Procesar reglas de filtro
            if 'reglas_filtro' in request.POST:
                try:
                    reglas = json.loads(request.POST['reglas_filtro'])
                    ConfiguracionService.guardar_reglas_filtro(configuracion, reglas)
                except json.JSONDecodeError:
                    return JsonResponse({'success': False, 'message': 'Error en el formato de las reglas de filtro'})
                
            return JsonResponse({'success': True, 'message': 'Configuración de correo guardada con éxito'})
            
        elif tab == 'seguridad':
            # Procesar formulario de seguridad
            form_data = {
                'req_mayusculas': request.POST.get('req_mayusculas') == 'true',
                'req_numeros': request.POST.get('req_numeros') == 'true',
                'req_especiales': request.POST.get('req_especiales') == 'true',
                'longitud_min_password': int(request.POST.get('longitud_min_password', 8)),
                'intentos_bloqueo': int(request.POST.get('intentos_bloqueo', 5)),
                'desbloqueo_automatico': request.POST.get('desbloqueo_automatico') == 'true',
                'metodo_2fa': request.POST.get('metodo_2fa', 'disabled'),
            }
            
            configuracion = ConfiguracionService.guardar_configuracion_seguridad(tenant, form_data, request.user)
                
            # Procesar rangos IP
            if 'rangos_ip' in request.POST:
                try:
                    rangos = json.loads(request.POST['rangos_ip'])
                    ConfiguracionService.guardar_rangos_ip(configuracion, rangos)
                except json.JSONDecodeError:
                    return JsonResponse({'success': False, 'message': 'Error en el formato de los rangos IP'})
                
            return JsonResponse({'success': True, 'message': 'Configuración de seguridad guardada con éxito'})
        
        # Si llegamos aquí, hubo un error
        return JsonResponse({'success': False, 'message': 'Error al guardar la configuración'})