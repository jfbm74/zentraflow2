# apps/ingesta_correo/urls.py - Actualizado para incluir rutas de ingesta programada

from django.urls import path, include
from .views import DashboardIngestaView, ApiDashboardIngestaView, ToggleServicioView, CorreosListView, VerifyConnectionView
# Comentado temporalmente hasta implementar el modelo ReglaFiltrado
# from .views_reglas import ReglasFiltradoView, ReglaFiltradoApiView, ReglaEstadoView, ReglasReordenarView
# from .views_reglas_test import TestReglaView, TestReglaExistenteView

# Definir el namespace
app_name = 'ingesta_correo'

urlpatterns = [
    # Vistas web
    path('', DashboardIngestaView.as_view(), name='dashboard'),
    path('correos/', CorreosListView.as_view(), name='correos_list'),
    # Comentado temporalmente hasta implementar el modelo ReglaFiltrado
    # path('reglas/', ReglasFiltradoView.as_view(), name='reglas'),
    
    # Incluir URLs de ingesta programada
    path('', include('apps.ingesta_correo.urls_ingesta')),
    
    # Incluir URLs de reglas de filtrado
    path('', include('apps.ingesta_correo.urls_reglas')),
    
    # API endpoints
    path('api/dashboard/', ApiDashboardIngestaView.as_view(), name='api_ingesta_dashboard'),
    path('api/tendencias/', ApiDashboardIngestaView.as_view(), name='api_tendencias'),
    path('api/toggle-servicio/', ToggleServicioView.as_view(), name='api_toggle_servicio'),
    path('api/verify-connection/', VerifyConnectionView.as_view(), name='api_verify_connection'),
    
    # Comentado temporalmente hasta implementar el modelo ReglaFiltrado
    # # API endpoints para reglas de filtrado
    # path('api/reglas/', ReglaFiltradoApiView.as_view(), name='api_reglas'),
    # path('api/reglas/<int:regla_id>/', ReglaFiltradoApiView.as_view(), name='api_regla_detalle'),
    # path('api/reglas/<int:regla_id>/estado/', ReglaEstadoView.as_view(), name='api_regla_estado'),
    # path('api/reglas/reordenar/', ReglasReordenarView.as_view(), name='api_reglas_reordenar'),
    
    # # API endpoints para prueba de reglas
    # path('api/reglas/test/', TestReglaView.as_view(), name='api_regla_test'),
    # path('api/reglas/<int:regla_id>/test/', TestReglaExistenteView.as_view(), name='api_regla_existente_test'),
]