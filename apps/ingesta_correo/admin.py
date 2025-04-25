from django.contrib import admin
from django.utils.html import format_html
from .models import (
    ServicioIngesta, 
    HistorialEjecucion, 
    CorreoIngesta,
    ArchivoAdjunto,
    LogActividad,
    EstadisticaDiaria,
    ReglaFiltrado,
    CondicionRegla,
    HistorialAplicacionRegla,
    CategoriaRegla,
    RegistroLogRegla
)

@admin.register(ServicioIngesta)
class ServicioIngestaAdmin(admin.ModelAdmin):
    list_display = ('tenant', 'nombre', 'activo', 'intervalo_minutos', 'ultima_ejecucion', 'en_ejecucion')
    list_filter = ('activo', 'en_ejecucion', 'tenant')
    search_fields = ('nombre', 'descripcion')
    readonly_fields = ('ultima_ejecucion', 'proxima_ejecucion', 'ultima_verificacion', 'fecha_creacion', 'fecha_modificacion')
    fieldsets = (
        ('Información General', {
            'fields': ('tenant', 'nombre', 'descripcion', 'activo')
        }),
        ('Configuración', {
            'fields': ('intervalo_minutos',)
        }),
        ('Estado', {
            'fields': ('en_ejecucion', 'ultima_ejecucion', 'proxima_ejecucion', 'ultima_verificacion')
        }),
        ('Auditoría', {
            'fields': ('fecha_creacion', 'fecha_modificacion', 'modificado_por')
        }),
    )

@admin.register(HistorialEjecucion)
class HistorialEjecucionAdmin(admin.ModelAdmin):
    list_display = ('servicio', 'fecha_inicio', 'fecha_fin', 'estado', 'correos_procesados', 'glosas_extraidas')
    list_filter = ('estado', 'tenant')
    search_fields = ('servicio__nombre',)
    readonly_fields = ('fecha_inicio', 'fecha_fin', 'duracion_segundos')
    fieldsets = (
        ('Información General', {
            'fields': ('tenant', 'servicio')
        }),
        ('Estado y Tiempos', {
            'fields': ('estado', 'fecha_inicio', 'fecha_fin', 'duracion_segundos')
        }),
        ('Resultados', {
            'fields': ('correos_procesados', 'correos_nuevos', 'archivos_procesados', 'glosas_extraidas')
        }),
        ('Detalles de Error', {
            'fields': ('mensaje_error', 'detalles')
        }),
    )

@admin.register(CorreoIngesta)
class CorreoIngestaAdmin(admin.ModelAdmin):
    list_display = ('asunto', 'remitente', 'fecha_recepcion', 'estado', 'glosas_extraidas')
    list_filter = ('estado', 'servicio__tenant')
    search_fields = ('asunto', 'remitente', 'mensaje_id')
    readonly_fields = ('fecha_recepcion', 'fecha_procesamiento')
    fieldsets = (
        ('Información del Correo', {
            'fields': ('servicio', 'mensaje_id', 'remitente', 'destinatarios', 'asunto')
        }),
        ('Contenido', {
            'fields': ('contenido_plano', 'contenido_html')
        }),
        ('Estado', {
            'fields': ('estado', 'fecha_recepcion', 'fecha_procesamiento', 'glosas_extraidas')
        }),
        ('Error', {
            'fields': ('error',)
        }),
    )

@admin.register(ArchivoAdjunto)
class ArchivoAdjuntoAdmin(admin.ModelAdmin):
    list_display = ('nombre_archivo', 'correo', 'tipo_contenido', 'tamaño', 'procesado')
    list_filter = ('procesado', 'tipo_contenido')
    search_fields = ('nombre_archivo', 'correo__asunto')
    readonly_fields = ('fecha_procesamiento',)

@admin.register(LogActividad)
class LogActividadAdmin(admin.ModelAdmin):
    list_display = ('evento', 'fecha_hora', 'tenant', 'estado')
    list_filter = ('evento', 'estado', 'tenant')
    search_fields = ('detalles', 'evento')
    readonly_fields = ('fecha_hora',)

@admin.register(EstadisticaDiaria)
class EstadisticaDiariaAdmin(admin.ModelAdmin):
    list_display = ('tenant', 'fecha', 'correos_procesados', 'glosas_extraidas', 'pendientes', 'errores')
    list_filter = ('tenant', 'fecha')
    search_fields = ('tenant__name',)

class CondicionReglaInline(admin.TabularInline):
    """Inline para editar condiciones de una regla compuesta."""
    model = CondicionRegla
    extra = 1
    fields = ('campo', 'condicion', 'valor', 'orden')
    ordering = ('orden',)

@admin.register(ReglaFiltrado)
class ReglaFiltradoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'servicio', 'tipo_regla', 'display_condicion', 'accion', 'display_activa', 'prioridad', 'conteo_usos')
    list_filter = ('activa', 'es_compuesta', 'accion', 'servicio__tenant', 'categoria')
    search_fields = ('nombre', 'descripcion', 'valor')
    readonly_fields = ('creado_en', 'modificado_en', 'conteo_usos', 'ultima_aplicacion')
    inlines = [CondicionReglaInline]
    save_on_top = True
    
    fieldsets = (
        ('Información General', {
            'fields': ('servicio', 'nombre', 'descripcion', 'categoria', 'activa', 'prioridad')
        }),
        ('Temporalidad', {
            'fields': ('fecha_inicio', 'fecha_fin'),
            'classes': ('collapse',),
        }),
        ('Configuración de Regla', {
            'fields': ('es_compuesta', 'operador_logico'),
            'description': 'Seleccione si esta regla utilizará múltiples condiciones.'
        }),
        ('Condición Simple', {
            'fields': ('campo', 'condicion', 'valor'),
            'classes': ('regla-simple',),
            'description': 'Configure la condición simple si la regla no es compuesta.'
        }),
        ('Acción', {
            'fields': ('accion', 'parametros_accion'),
            'description': 'Seleccione la acción que se ejecutará cuando se cumpla la regla.'
        }),
        ('Estadísticas', {
            'fields': ('conteo_usos', 'ultima_aplicacion'),
            'classes': ('collapse',),
        }),
        ('Auditoría', {
            'fields': ('creado_en', 'modificado_en', 'creado_por', 'modificado_por'),
            'classes': ('collapse',),
        }),
    )
    
    def tipo_regla(self, obj):
        """Muestra el tipo de regla (simple o compuesta)."""
        if obj.es_compuesta:
            return format_html('<span style="color: #3498db;">Compuesta ({})</span>', obj.get_operador_logico_display())
        return 'Simple'
    tipo_regla.short_description = 'Tipo'
    
    def display_condicion(self, obj):
        """Muestra un resumen de la condición de la regla."""
        if obj.es_compuesta:
            condiciones = obj.condiciones.all()
            if not condiciones:
                return '-'
            return format_html("<small>{} condiciones</small>", condiciones.count())
        else:
            if not obj.campo or not obj.condicion or not obj.valor:
                return '-'
            return format_html("{} {} <strong>{}</strong>", 
                               obj.get_campo_display(), 
                               obj.get_condicion_display(), 
                               obj.valor)
    display_condicion.short_description = 'Condición'
    
    def display_activa(self, obj):
        """Muestra un indicador visual del estado de la regla."""
        if obj.activa:
            return format_html('<span style="color: green;">✓</span>')
        return format_html('<span style="color: red;">✗</span>')
    display_activa.short_description = 'Activa'
    
    class Media:
        js = ('js/admin/regla_filtrado.js',)
        css = {
            'all': ('css/admin/regla_filtrado.css',)
        }

@admin.register(CategoriaRegla)
class CategoriaReglaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'servicio', 'color_display', 'count_reglas')
    list_filter = ('servicio__tenant', 'servicio')
    search_fields = ('nombre', 'descripcion')
    
    def color_display(self, obj):
        """Muestra un cuadrado con el color de la categoría."""
        return format_html('<div style="width: 20px; height: 20px; background-color: {}; border-radius: 3px;"></div>', obj.color)
    color_display.short_description = 'Color'
    
    def count_reglas(self, obj):
        """Muestra el número de reglas en esta categoría."""
        return obj.reglas.count()
    count_reglas.short_description = 'Reglas'

@admin.register(HistorialAplicacionRegla)
class HistorialAplicacionReglaAdmin(admin.ModelAdmin):
    list_display = ('regla', 'correo', 'fecha_aplicacion', 'resultado_display', 'accion_ejecutada')
    list_filter = ('resultado', 'fecha_aplicacion', 'regla__servicio__tenant')
    search_fields = ('regla__nombre', 'correo__asunto')
    readonly_fields = ('regla', 'correo', 'fecha_aplicacion', 'resultado', 'accion_ejecutada', 'detalles')
    
    def resultado_display(self, obj):
        """Muestra el resultado con un formato visual."""
        if obj.resultado:
            return format_html('<span style="color: green;">Se cumplió</span>')
        return format_html('<span style="color: red;">No se cumplió</span>')
    resultado_display.short_description = 'Resultado'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False

@admin.register(RegistroLogRegla)
class RegistroLogReglaAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'nivel_display', 'mensaje_corto', 'tenant', 'regla', 'correo')
    list_filter = ('nivel', 'timestamp', 'tenant', 'regla__servicio__tenant')
    search_fields = ('mensaje', 'regla__nombre', 'correo__asunto')
    readonly_fields = ('timestamp', 'nivel', 'mensaje', 'tenant', 'regla', 'correo', 'datos_contexto_display')
    date_hierarchy = 'timestamp'
    ordering = ('-timestamp',)
    
    def nivel_display(self, obj):
        """Muestra el nivel de log con un formato visual."""
        colores = {
            'INFO': 'blue',
            'DEBUG': 'gray',
            'WARNING': 'orange',
            'ERROR': 'red',
            'TRACE': 'purple'
        }
        color = colores.get(obj.nivel, 'black')
        return format_html('<span style="color: {};">{}</span>', color, obj.nivel)
    nivel_display.short_description = 'Nivel'
    
    def mensaje_corto(self, obj):
        """Muestra un resumen del mensaje."""
        return obj.mensaje[:100] + '...' if len(obj.mensaje) > 100 else obj.mensaje
    mensaje_corto.short_description = 'Mensaje'
    
    def datos_contexto_display(self, obj):
        """Muestra los datos de contexto en formato JSON legible."""
        if not obj.datos_contexto:
            return '-'
        import json
        return format_html('<pre>{}</pre>', json.dumps(obj.datos_contexto, indent=2))
    datos_contexto_display.short_description = 'Datos de Contexto'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    class Media:
        css = {
            'all': ('css/admin/registro_log_regla.css',)
        }
