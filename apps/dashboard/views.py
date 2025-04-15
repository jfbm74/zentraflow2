from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

class DashboardView(LoginRequiredMixin, TemplateView):
    """Vista para el dashboard principal de ZentraFlow."""
    template_name = "dashboard/dashboard.html"
    login_url = '/auth/login/'  # Redirigir al login si el usuario no está autenticado
    
    def get_context_data(self, **kwargs):
        """Añadir datos de contexto para la plantilla."""
        context = super().get_context_data(**kwargs)
        context['active_menu'] = 'dashboard'  # Para marcar como activo el ítem del menú
        
        # Otros datos del dashboard se podrían añadir aquí
        # Por ahora usamos datos de ejemplo (dummy data)
        
        return context