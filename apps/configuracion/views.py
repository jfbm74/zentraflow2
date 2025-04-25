import json
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.tenants.models import Tenant  # Change this line
from .forms import TenantConfigForm
from .services.config_service import ConfigService
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from .models import TenantConfig, EmailConfig
from .services.email_config_service import EmailConfigService




class ConfiguracionView(LoginRequiredMixin, TemplateView):
    """Vista principal para la sección de configuración."""
    
    template_name = "configuracion/configuracion.html"
    
    def get_context_data(self, **kwargs):
        """Añade el tenant actual y datos adicionales al contexto."""
        context = super().get_context_data(**kwargs)
        context['active_menu'] = 'configuracion'
        
        # Si es super admin, mostrar listado de tenants
        if self.request.user.is_superuser or self.request.user.role == 'ADMIN':
            context['tenants'] = Tenant.objects.filter(is_active=True)
            
        # Determinar el tenant actual basado en la URL o usuario
        tenant_id = kwargs.get('tenant_id')
        if tenant_id and (self.request.user.is_superuser or self.request.user.role == 'ADMIN'):
            context['current_tenant'] = Tenant.objects.get(id=tenant_id, is_active=True)
        else:
            context['current_tenant'] = self.request.user.tenant
        
        # Obtener configuración del tenant
        context['tenant_config'] = ConfigService.get_tenant_config(context['current_tenant'])
        
        # Comprobar si el usuario puede editar la configuración
        context['is_editable'] = (self.request.user.is_superuser or 
                                  self.request.user.role == 'ADMIN' and 
                                  self.request.user.tenant == context['current_tenant'])
        
        context['is_super_admin'] = self.request.user.is_superuser
        
        return context
    
    def post(self, request, *args, **kwargs):
        """Maneja solicitudes POST para guardar la configuración."""
        # Verificar si el usuario tiene permisos
        if not (request.user.is_superuser or request.user.role == 'ADMIN'):
            return JsonResponse({'success': False, 'message': 'No tiene permisos para editar la configuración'}, status=403)
        
        # Determinar el tenant actual basado en la URL o usuario
        tenant_id = kwargs.get('tenant_id')
        if tenant_id and (request.user.is_superuser or request.user.role == 'ADMIN'):
            tenant = Tenant.objects.get(id=tenant_id, is_active=True)
        else:
            tenant = request.user.tenant
        
        # Determinar la acción a realizar
        action = request.POST.get('action', '')
        
        # Acciones para la configuración del tenant (logo, información general)
        if action == 'remove_logo':
            # Eliminar logo
            config = ConfigService.get_tenant_config(tenant)
            result = ConfigService.remove_tenant_logo(config)
            return JsonResponse(result)
        
        elif action == 'save_email_config':
            # Guardar configuración de correo
            result = EmailConfigService.update_email_config(
                tenant=tenant,
                data=request.POST,
                user=request.user
            )
            # Eliminar el objeto EmailConfig del resultado para evitar error de serialización
            if 'config' in result:
                del result['config']
            return JsonResponse(result)
        
        elif action == 'test_connection':
            # Probar conexión de correo
            result = EmailConfigService.test_connection(request.POST)
            return JsonResponse(result)
        
        elif action == 'sync_now':
            # Iniciar sincronización manual
            # Aquí se debería implementar la lógica para iniciar la sincronización
            # como una tarea asíncrona
            return JsonResponse({
                'success': True,
                'message': 'Sincronización iniciada correctamente'
            })
        
        else:
            # Por defecto, actualizar configuración general del tenant
            result = ConfigService.update_tenant_config(
                tenant=tenant,
                user=request.user,
                data=request.POST,
                files=request.FILES
            )
            
            if result['success'] and 'config' in result:
                # Si se actualizó correctamente, devolver la URL del logo si existe
                config = result['config']
                if config.logo:
                    result['logo_url'] = config.logo.url
            
            return JsonResponse(result)