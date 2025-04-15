from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from tenants.models import Tenant

class ConfiguracionView(LoginRequiredMixin, TemplateView):
    """Vista para la configuración del cliente (tenant)."""
    template_name = "configuracion/configuracion.html"
    login_url = '/auth/login/'
    
    def get_context_data(self, **kwargs):
        """Añadir datos de contexto para la plantilla."""
        context = super().get_context_data(**kwargs)
        context['active_menu'] = 'configuracion'  # Para marcar como activo el ítem del menú
        
        # El tenant actual siempre es el del usuario 
        context['current_tenant'] = self.request.user.tenant
        
        # Para Super Admin, cargar todos los tenants
        if self.request.user.is_superuser or self.request.user.role == 'ADMIN':
            context['tenants'] = Tenant.objects.filter(is_active=True).order_by('name')
            context['is_super_admin'] = self.request.user.is_superuser
            context['is_editable'] = True
        else:
            context['is_editable'] = False
            
        return context