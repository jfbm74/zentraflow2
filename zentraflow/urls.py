
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

from apps.dashboard.views import DashboardView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("authentication.api.urls")),
    path("auth/", include("authentication.web.urls")),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("configuracion/", include("configuracion.urls")),
    path("", RedirectView.as_view(url="/dashboard/", permanent=False), name="home"),
]

# Servir archivos estáticos en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)