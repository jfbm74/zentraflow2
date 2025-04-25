from django.urls import path
from .views_reglas import (
    ReglasFiltradoView, 
    ReglaFiltradoApiView, 
    ReglaEstadoView, 
    ReglasReordenarView,
    ReglaCrearView,
    ReglaEditarView,
    ReglaEliminarView,
    # Mantener las vistas de categorías como funciones
    categorias_list,
    categoria_create,
    categoria_edit,
    categoria_delete
)
from .views_reglas_test import TestReglaView, TestReglaExistenteView

# Namespace: 'ingesta_correo'
urlpatterns = [
    # Vistas web para reglas de filtrado (basadas en clases)
    path('reglas/', ReglasFiltradoView.as_view(), name='reglas'),
    path('reglas/crear/', ReglaCrearView.as_view(), name='regla_crear'),
    path('reglas/editar/<int:regla_id>/', ReglaEditarView.as_view(), name='regla_editar'),
    path('reglas/eliminar/<int:regla_id>/', ReglaEliminarView.as_view(), name='regla_eliminar'),
    
    # Vistas antiguas basadas en funciones (para retrocompatibilidad)
    path('reglas/detalles/<int:regla_id>/', ReglaEditarView.as_view(), name='regla_detail'),
    
    # API endpoints para reglas de filtrado
    path('api/reglas/', ReglaFiltradoApiView.as_view(), name='api_reglas'),
    path('api/reglas/<int:regla_id>/', ReglaFiltradoApiView.as_view(), name='api_regla_detalle'),
    path('api/reglas/<int:regla_id>/estado/', ReglaEstadoView.as_view(), name='api_regla_estado'),
    path('api/reglas/reordenar/', ReglasReordenarView.as_view(), name='api_reglas_reordenar'),
    
    # API endpoints para prueba de reglas
    path('api/reglas/test/', TestReglaView.as_view(), name='api_regla_test'),
    path('api/reglas/<int:regla_id>/test/', TestReglaExistenteView.as_view(), name='api_regla_existente_test'),
    
    # Categorías de reglas (basadas en funciones)
    path('categorias/', categorias_list, name='categorias_list'),
    path('categorias/nueva/', categoria_create, name='categoria_create'),
    path('categorias/<int:categoria_id>/editar/', categoria_edit, name='categoria_edit'),
    path('categorias/<int:categoria_id>/eliminar/', categoria_delete, name='categoria_delete'),
] 