# apps/ingesta_correo/admin.py
from django.contrib import admin
from .models import (
    ServicioIngesta, 
    ReglaFiltrado, 
    CorreoIngesta, 
    ArchivoAdjunto, 
    EstadisticaDiaria, 
    LogActividad,
    HistorialEjecucion
)

@admin.register(ServicioIngesta)
class ServicioIngestaAdmin(admin.ModelAdmin):
    """Configuración admin para el modelo ServicioIngesta."""
    list_display = ('tenant', 'activo', 'ultima_verificacion', 'modificado_en')
    list_filter = ('activo',)
    search_fields = ('tenant__name',)
    ordering = ('tenant__name',)

@admin.register(ReglaFiltrado)
class ReglaFiltradoAdmin(admin.ModelAdmin):
    """Configuración admin para el modelo ReglaFiltrado."""
    list_display = ('nombre', 'servicio', 'campo', 'condicion', 'valor', 'accion', 'activa', 'prioridad')
    list_filter = ('activa', 'campo', 'condicion', 'accion')
    search_fields = ('nombre', 'valor', 'servicio__tenant__name')
    ordering = ('servicio__tenant__name', 'prioridad')

@admin.register(CorreoIngesta)
class CorreoIngestaAdmin(admin.ModelAdmin):
    """Configuración admin para el modelo CorreoIngesta."""
    list_display = ('remitente', 'asunto', 'fecha_recepcion', 'estado', 'glosas_extraidas')
    list_filter = ('estado', 'fecha_recepcion')
    search_fields = ('remitente', 'asunto', 'mensaje_id')
    ordering = ('-fecha_recepcion',)
    date_hierarchy = 'fecha_recepcion'

@admin.register(ArchivoAdjunto)
class ArchivoAdjuntoAdmin(admin.ModelAdmin):
    """Configuración admin para el modelo ArchivoAdjunto."""
    list_display = ('nombre_archivo', 'correo', 'tipo_contenido', 'tamaño', 'procesado')
    list_filter = ('procesado', 'tipo_contenido')
    search_fields = ('nombre_archivo', 'correo__asunto')
    ordering = ('-creado_en',)

@admin.register(EstadisticaDiaria)
class EstadisticaDiariaAdmin(admin.ModelAdmin):
    """Configuración admin para el modelo EstadisticaDiaria."""
    list_display = ('tenant', 'fecha', 'correos_procesados', 'glosas_extraidas', 'pendientes', 'errores')
    list_filter = ('fecha',)
    search_fields = ('tenant__name',)
    ordering = ('-fecha', 'tenant__name')
    date_hierarchy = 'fecha'

@admin.register(LogActividad)
class LogActividadAdmin(admin.ModelAdmin):
    """Configuración admin para el modelo LogActividad."""
    list_display = ('fecha_hora', 'tenant', 'evento', 'detalles', 'estado')
    list_filter = ('evento', 'fecha_hora')
    search_fields = ('detalles', 'tenant__name')
    ordering = ('-fecha_hora',)
    date_hierarchy = 'fecha_hora'

@admin.register(HistorialEjecucion)
class HistorialEjecucionAdmin(admin.ModelAdmin):
    """Configuración admin para el modelo HistorialEjecucion."""
    list_display = ('servicio', 'tenant', 'fecha_inicio', 'fecha_fin', 'duracion_segundos', 'estado', 
                   'correos_procesados', 'glosas_extraidas')
    list_filter = ('estado', 'fecha_inicio')
    search_fields = ('servicio__tenant__name', 'mensaje_error')
    ordering = ('-fecha_inicio',)
    date_hierarchy = 'fecha_inicio'
    readonly_fields = ('fecha_inicio', 'fecha_fin', 'duracion_segundos')