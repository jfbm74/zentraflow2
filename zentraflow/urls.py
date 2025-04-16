from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from apps.configuracion.views import ConfiguracionView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from apps.dashboard.views import DashboardView

urlpatterns = [
    path("admin/", admin.site.urls),
    # Change this from "authentication.api.urls" to "apps.authentication.api.urls"
    path("api/auth/", include("apps.authentication.api.urls")),
    # Change this from "authentication.web.urls" to "apps.authentication.web.urls"
    path("auth/", include("apps.authentication.web.urls")),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("configuracion/", include("apps.configuracion.urls")),
    path("", RedirectView.as_view(url="/dashboard/", permanent=False), name="home"),
    path('<int:tenant_id>/', ConfiguracionView.as_view(), name='configuracion_tenant'),
    
    # API endpoints - Change this from "configuracion.api.urls" to "apps.configuracion.api.urls"
    path('api/', include('apps.configuracion.api.urls')),
]

# Servir archivos estáticos en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)