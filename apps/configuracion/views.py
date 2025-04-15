from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from tenants.models import Tenant
from .forms import TenantConfigForm
from .services.config_service import ConfigService
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.http import JsonResponse




class ConfiguracionView(LoginRequiredMixin, TemplateView):
    """Vista para la configuración del cliente (tenant)."""
    template_name = "configuracion/configuracion.html"
    login_url = '/auth/login/'
    
    def get_context_data(self, **kwargs):
        """Añadir datos de contexto para la plantilla."""
        context = super().get_context_data(**kwargs)
        context['active_menu'] = 'configuracion'
        
        # Si se proporciona un tenant_id en la URL, intentar obtener ese tenant
        tenant_id = self.kwargs.get('tenant_id')
        if tenant_id and (self.request.user.is_superuser or self.request.user.role == 'ADMIN'):
            tenant = get_object_or_404(Tenant, id=tenant_id, is_active=True)
        else:
            # Por defecto, usar el tenant del usuario
            tenant = self.request.user.tenant
            
        context['current_tenant'] = tenant
        
        # Obtener configuración del tenant
        tenant_config = ConfigService.get_tenant_config(tenant)
        context['tenant_config'] = tenant_config
        
        # Para Super Admin, cargar todos los tenants
        if self.request.user.is_superuser or self.request.user.role == 'ADMIN':
            context['tenants'] = Tenant.objects.filter(is_active=True).order_by('name')
            context['is_super_admin'] = self.request.user.is_superuser
            context['is_editable'] = True
        else:
            context['is_editable'] = False
            
        return context
    
    def post(self, request, *args, **kwargs):
        """Procesar formulario de configuración."""
        # Determinar el tenant a actualizar
        tenant_id = kwargs.get('tenant_id')
        if tenant_id and (request.user.is_superuser or request.user.role == 'ADMIN'):
            tenant = get_object_or_404(Tenant, id=tenant_id, is_active=True)
        else:
            tenant = request.user.tenant
        
        # Verificar permisos de edición
        if not (request.user.is_superuser or request.user.role == 'ADMIN'):
            return JsonResponse({
                'success': False,
                'message': 'No tiene permisos para editar la configuración.'
            }, status=403)
        
        # Verificar el tipo de acción
        action = request.POST.get('action')
        if action == 'remove_logo':
            # Eliminar logo
            config = ConfigService.get_tenant_config(tenant)
            result = ConfigService.remove_tenant_logo(config)
            return JsonResponse(result)
        else:
            # Actualizar configuración
            form = TenantConfigForm(request.POST, request.FILES)
            if form.is_valid():
                result = ConfigService.update_tenant_config(
                    tenant=tenant,
                    user=request.user,
                    data=form.cleaned_data,
                    files=request.FILES
                )
                return JsonResponse(result)
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Formulario inválido',
                    'errors': form.errors
                }, status=400)