# apps/ingesta_correo/urls_ingesta.py

from django.urls import path
from .views_ingesta import (
    IngestaControlPanelView,
    ApiServicioIngestaView,
    HistorialIngestaView,
    ApiHistorialDetalleView
)

urlpatterns = [
    # Vistas web
    path('programada/', IngestaControlPanelView.as_view(), name='control_panel'),
    path('historial/', HistorialIngestaView.as_view(), name='historial_ingesta'),
    
    # API endpoints
    path('api/servicio/', ApiServicioIngestaView.as_view(), name='api_servicio_ingesta'),
    path('api/historial/<int:historial_id>/', ApiHistorialDetalleView.as_view(), name='api_historial_detalle'),
]