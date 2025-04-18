
from django.urls import path
from .views import DashboardIngestaView, ApiDashboardIngestaView, ToggleServicioView, CorreosListView, VerifyConnectionView

urlpatterns = [
    # Vistas web
    path('', DashboardIngestaView.as_view(), name='ingesta_correo_dashboard'),
    path('correos/', CorreosListView.as_view(), name='ingesta_correo_correos'),
    
    # API endpoints
    path('api/dashboard/', ApiDashboardIngestaView.as_view(), name='api_ingesta_dashboard'),
    path('api/toggle-servicio/', ToggleServicioView.as_view(), name='api_toggle_servicio'),
    path('api/verify-connection/', VerifyConnectionView.as_view(), name='api_verify_connection'),
]