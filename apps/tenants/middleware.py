from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponseRedirect
from django.urls import reverse, resolve
from django.conf import settings
import re

class TenantMiddleware(MiddlewareMixin):
    """
    Middleware que maneja la identificación del tenant basada en el dominio.
    """
    def process_request(self, request):
        """
        Procesa cada solicitud para determinar el tenant basado en el dominio.
        """
        # Lista de URLs que no requieren tenant (login, registro, etc.)
        public_urls = [
            reverse('login'),
            reverse('password_reset'),
            # Agregar otras URLs públicas aquí
        ]
        
        # Lista de patrones de URLs públicas (para endpoints de API, etc.)
        public_patterns = [
            r'^/api/auth/token/',
            r'^/static/',
            r'^/admin/',
            # Agregar otros patrones públicos aquí
        ]
        
        # Verificar si la URL actual es pública
        current_url = request.path_info
        if current_url in public_urls or any(re.match(pattern, current_url) for pattern in public_patterns):
            return None
        
        # Si el usuario no está autenticado, redirigir al login
        if not request.user.is_authenticated:
            return HttpResponseRedirect(reverse('login'))
        
        # Si el usuario está autenticado, asegurarse de que tenga un tenant
        tenant = getattr(request.user, 'tenant', None)
        if not tenant:
            # Esto no debería ocurrir si el usuario está autenticado correctamente
            return HttpResponseRedirect(reverse('login'))
        
        # Añadir el tenant a la solicitud para uso posterior
        request.tenant = tenant
        return None