# apps/ingesta_correo/models.py
from django.utils import timezone
from datetime import timedelta
from django.db import models
from apps.tenants.models import Tenant
from apps.authentication.models import ZentraflowUser

class ServicioIngesta(models.Model):
    """Configuración principal del servicio de ingesta de correo."""
    tenant = models.OneToOneField('tenants.Tenant', on_delete=models.CASCADE, related_name='servicio_ingesta')
    activo = models.BooleanField(default=True, verbose_name="Activo")
    
    # Nuevos campos para la programación
    intervalo_minutos = models.PositiveIntegerField(default=15, verbose_name="Intervalo (minutos)",
                                               help_text="Intervalo de tiempo entre verificaciones")
    proxima_ejecucion = models.DateTimeField(null=True, blank=True, verbose_name="Próxima ejecución programada")
    ultima_ejecucion = models.DateTimeField(null=True, blank=True, verbose_name="Última ejecución")
    ultima_verificacion = models.DateTimeField(null=True, blank=True, verbose_name="Última verificación")
    
    # Control de ejecución
    en_ejecucion = models.BooleanField(default=False, verbose_name="En ejecución", 
                                    help_text="Indica si el servicio está actualmente ejecutándose")
    tareas_pendientes = models.PositiveIntegerField(default=0, verbose_name="Tareas pendientes")
    
    # Métricas
    correos_procesados_total = models.PositiveIntegerField(default=0, verbose_name="Total de correos procesados")
    correos_ultima_ejecucion = models.PositiveIntegerField(default=0, verbose_name="Correos en última ejecución")
    
    # Control de cambios
    creado_en = models.DateTimeField(auto_now_add=True, verbose_name="Creado en")
    modificado_en = models.DateTimeField(auto_now=True, verbose_name="Modificado en")
    modificado_por = models.ForeignKey('authentication.ZentraflowUser', on_delete=models.SET_NULL, 
                                       null=True, blank=True, related_name='servicios_modificados')

    class Meta:
        app_label = 'ingesta_correo'
        verbose_name = "Servicio de Ingesta"
        verbose_name_plural = "Servicios de Ingesta"

    def __str__(self):
        return f"Servicio de Ingesta para {self.tenant.name}"
    
    def actualizar_proxima_ejecucion(self):
        """Calcula y actualiza la próxima ejecución programada basada en el intervalo."""
        now = timezone.now()
        
        # Si no hay próxima ejecución programada, o ya ha pasado, programar desde ahora
        if not self.proxima_ejecucion or self.proxima_ejecucion <= now:
            self.proxima_ejecucion = now + timedelta(minutes=self.intervalo_minutos)
        
        self.save(update_fields=['proxima_ejecucion'])
        return self.proxima_ejecucion
    
    def tiempo_hasta_proxima_ejecucion(self):
        """Retorna el tiempo restante hasta la próxima ejecución en formato legible."""
        if not self.proxima_ejecucion:
            return "No programado"
            
        now = timezone.now()
        if self.proxima_ejecucion <= now:
            return "Pendiente"
            
        delta = self.proxima_ejecucion - now
        minutes, seconds = divmod(delta.seconds, 60)
        hours, minutes = divmod(minutes, 60)
        
        if delta.days > 0:
            return f"{delta.days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m {seconds}s"
    
    def registrar_ejecucion(self, correos_procesados=0):
        """Registra que se ha completado una ejecución del servicio."""
        self.ultima_ejecucion = timezone.now()
        self.correos_ultima_ejecucion = correos_procesados
        self.correos_procesados_total += correos_procesados
        
        # Asegurar que el estado de ejecución se limpie
        self.en_ejecucion = False
        
        # Solo actualizar próxima ejecución si el servicio sigue activo
        if self.activo:
            self.actualizar_proxima_ejecucion()
        else:
            self.proxima_ejecucion = None
            
        self.save(update_fields=[
            'ultima_ejecucion', 'correos_ultima_ejecucion', 
            'correos_procesados_total', 'en_ejecucion', 'proxima_ejecucion'
        ])
    
    def iniciar_ejecucion(self):
        """Marca el servicio como en ejecución."""
        # Solo iniciar si no está ya en ejecución
        if not self.en_ejecucion:
            self.en_ejecucion = True
            self.ultima_verificacion = timezone.now()
            self.save(update_fields=['en_ejecucion', 'ultima_verificacion'])
            return True
        return False

class ReglaFiltrado(models.Model):
    """Reglas para filtrar correos entrantes."""
    
    class TipoCampo(models.TextChoices):
        ASUNTO = 'ASUNTO', 'Asunto'
        REMITENTE = 'REMITENTE', 'Remitente'
        DESTINATARIO = 'DESTINATARIO', 'Destinatario'
        CONTENIDO = 'CONTENIDO', 'Contenido'
        ADJUNTO = 'ADJUNTO', 'Nombre de adjunto'
    
    class TipoCondicion(models.TextChoices):
        CONTIENE = 'CONTIENE', 'Contiene'
        NO_CONTIENE = 'NO_CONTIENE', 'No contiene'
        ES_IGUAL = 'ES_IGUAL', 'Es igual a'
        EMPIEZA_CON = 'EMPIEZA_CON', 'Empieza con'
        TERMINA_CON = 'TERMINA_CON', 'Termina con'
        COINCIDE_REGEX = 'COINCIDE_REGEX', 'Coincide con regex'
    
    class TipoAccion(models.TextChoices):
        PROCESAR = 'PROCESAR', 'Procesar'
        IGNORAR = 'IGNORAR', 'Ignorar'
        ARCHIVAR = 'ARCHIVAR', 'Archivar'
        ETIQUETAR = 'ETIQUETAR', 'Etiquetar'
    
    servicio = models.ForeignKey(ServicioIngesta, on_delete=models.CASCADE, related_name='reglas')
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    campo = models.CharField(max_length=20, choices=TipoCampo.choices, default=TipoCampo.ASUNTO, 
                            verbose_name="Campo")
    condicion = models.CharField(max_length=20, choices=TipoCondicion.choices, default=TipoCondicion.CONTIENE, 
                                verbose_name="Condición")
    valor = models.CharField(max_length=255, verbose_name="Valor")
    accion = models.CharField(max_length=20, choices=TipoAccion.choices, default=TipoAccion.PROCESAR, 
                             verbose_name="Acción")
    activa = models.BooleanField(default=True, verbose_name="Activa")
    prioridad = models.PositiveSmallIntegerField(default=0, verbose_name="Prioridad")
    creado_en = models.DateTimeField(auto_now_add=True, verbose_name="Creado en")
    modificado_en = models.DateTimeField(auto_now=True, verbose_name="Modificado en")
    creado_por = models.ForeignKey('authentication.ZentraflowUser', on_delete=models.SET_NULL, 
                                  null=True, blank=True, related_name='reglas_creadas')

    class Meta:
        app_label = 'ingesta_correo'
        verbose_name = "Regla de Filtrado"
        verbose_name_plural = "Reglas de Filtrado"
        ordering = ['prioridad', 'creado_en']

    def __str__(self):
        return f"{self.nombre} ({self.get_campo_display()} {self.get_condicion_display()} '{self.valor}')"


class CorreoIngesta(models.Model):
    """Registro de correos ingresados al sistema."""
    
    class Estado(models.TextChoices):
        PENDIENTE = 'PENDIENTE', 'Pendiente'
        PROCESADO = 'PROCESADO', 'Procesado'
        ERROR = 'ERROR', 'Error'
        IGNORADO = 'IGNORADO', 'Ignorado'
    
    servicio = models.ForeignKey(ServicioIngesta, on_delete=models.CASCADE, related_name='correos')
    mensaje_id = models.CharField(max_length=255, verbose_name="ID del mensaje", unique=True)
    remitente = models.CharField(max_length=255, verbose_name="Remitente")
    destinatarios = models.TextField(verbose_name="Destinatarios")
    asunto = models.CharField(max_length=255, verbose_name="Asunto")
    fecha_recepcion = models.DateTimeField(verbose_name="Fecha de recepción")
    contenido_plano = models.TextField(verbose_name="Contenido texto plano", null=True, blank=True)
    contenido_html = models.TextField(verbose_name="Contenido HTML", null=True, blank=True)
    regla_aplicada = models.ForeignKey(ReglaFiltrado, on_delete=models.SET_NULL, 
                                      null=True, blank=True, related_name='correos_procesados')
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PENDIENTE, 
                             verbose_name="Estado")
    fecha_procesamiento = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de procesamiento")
    mensaje_error = models.TextField(null=True, blank=True, verbose_name="Mensaje de error")
    marcado_leido = models.BooleanField(default=False, verbose_name="Marcado como leído")
    
    # Campos para estadísticas y seguimiento
    glosas_extraidas = models.PositiveIntegerField(default=0, verbose_name="Glosas extraídas")
    intentos_procesamiento = models.PositiveSmallIntegerField(default=0, verbose_name="Intentos de procesamiento")
    evento = models.CharField(max_length=100, default="Correo recibido", verbose_name="Evento")
    
    creado_en = models.DateTimeField(auto_now_add=True, verbose_name="Creado en")
    modificado_en = models.DateTimeField(auto_now=True, verbose_name="Modificado en")

    class Meta:
        app_label = 'ingesta_correo'
        verbose_name = "Correo Ingesta"
        verbose_name_plural = "Correos Ingesta"
        ordering = ['-fecha_recepcion']
        indexes = [
            models.Index(fields=['mensaje_id']),
            models.Index(fields=['remitente']),
            models.Index(fields=['asunto']),
            models.Index(fields=['estado']),
            models.Index(fields=['fecha_recepcion']),
        ]

    def __str__(self):
        return f"De: {self.remitente}, Asunto: {self.asunto}"


class ArchivoAdjunto(models.Model):
    """Archivos adjuntos de los correos."""
    correo = models.ForeignKey(CorreoIngesta, on_delete=models.CASCADE, related_name='adjuntos')
    nombre_archivo = models.CharField(max_length=255, verbose_name="Nombre del archivo")
    tipo_contenido = models.CharField(max_length=100, verbose_name="Tipo de contenido")
    tamaño = models.PositiveIntegerField(verbose_name="Tamaño en bytes")
    archivo = models.FileField(upload_to='correos/adjuntos/%Y/%m/%d/', verbose_name="Archivo")
    procesado = models.BooleanField(default=False, verbose_name="Procesado")
    fecha_procesamiento = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de procesamiento")
    resultado_procesamiento = models.TextField(null=True, blank=True, verbose_name="Resultado del procesamiento")
    
    creado_en = models.DateTimeField(auto_now_add=True, verbose_name="Creado en")

    class Meta:
        app_label = 'ingesta_correo'
        verbose_name = "Archivo Adjunto"
        verbose_name_plural = "Archivos Adjuntos"

    def __str__(self):
        return self.nombre_archivo


class EstadisticaDiaria(models.Model):
    """Estadísticas diarias de la ingesta de correos."""
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, related_name='estadisticas_ingesta')
    fecha = models.DateField(verbose_name="Fecha")
    correos_procesados = models.PositiveIntegerField(default=0, verbose_name="Correos procesados")
    glosas_extraidas = models.PositiveIntegerField(default=0, verbose_name="Glosas extraídas")
    pendientes = models.PositiveIntegerField(default=0, verbose_name="Pendientes")
    errores = models.PositiveIntegerField(default=0, verbose_name="Errores")
    
    creado_en = models.DateTimeField(auto_now_add=True, verbose_name="Creado en")
    actualizado_en = models.DateTimeField(auto_now=True, verbose_name="Actualizado en")

    class Meta:
        app_label = 'ingesta_correo'
        verbose_name = "Estadística Diaria"
        verbose_name_plural = "Estadísticas Diarias"
        unique_together = ['tenant', 'fecha']
        ordering = ['-fecha']

    def __str__(self):
        return f"Estadísticas de {self.tenant.name} para {self.fecha}"


class LogActividad(models.Model):
    """Registro de actividad del módulo de ingesta."""
    
    class TipoEvento(models.TextChoices):
        CORREO_RECIBIDO = 'CORREO_RECIBIDO', 'Correo recibido'
        ADJUNTO_EXTRAIDO = 'ADJUNTO_EXTRAIDO', 'Adjunto extraído'
        GLOSA_PROCESADA = 'GLOSA_PROCESADA', 'Glosa procesada'
        ERROR_PROCESAMIENTO = 'ERROR_PROCESAMIENTO', 'Error de procesamiento'
        SERVICIO_INICIADO = 'SERVICIO_INICIADO', 'Servicio iniciado'
        SERVICIO_DETENIDO = 'SERVICIO_DETENIDO', 'Servicio detenido'
        REGLA_CREADA = 'REGLA_CREADA', 'Regla creada'
        REGLA_MODIFICADA = 'REGLA_MODIFICADA', 'Regla modificada'
        REGLA_ELIMINADA = 'REGLA_ELIMINADA', 'Regla eliminada'
    
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, related_name='logs_ingesta')
    fecha_hora = models.DateTimeField(auto_now_add=True, verbose_name="Fecha/Hora")
    evento = models.CharField(max_length=30, choices=TipoEvento.choices, verbose_name="Evento")
    detalles = models.TextField(verbose_name="Detalles")
    usuario = models.ForeignKey('authentication.ZentraflowUser', on_delete=models.SET_NULL, 
                              null=True, blank=True, related_name='logs_ingesta')
    correo = models.ForeignKey(CorreoIngesta, on_delete=models.SET_NULL, 
                             null=True, blank=True, related_name='logs')
    estado = models.CharField(max_length=20, default='', verbose_name="Estado")

    class Meta:
        app_label = 'ingesta_correo'
        verbose_name = "Log de Actividad"
        verbose_name_plural = "Logs de Actividad"
        ordering = ['-fecha_hora']
        indexes = [
            models.Index(fields=['-fecha_hora']),
            models.Index(fields=['evento']),
            models.Index(fields=['tenant']),
        ]

    def __str__(self):
        return f"{self.fecha_hora} - {self.get_evento_display()}"

class HistorialEjecucion(models.Model):
    """Registro histórico de ejecuciones del servicio de ingesta."""
    
    class EstadoEjecucion(models.TextChoices):
        EXITOSO = 'EXITOSO', 'Exitoso'
        ERROR = 'ERROR', 'Error'
        PARCIAL = 'PARCIAL', 'Parcialmente exitoso'
        CANCELADO = 'CANCELADO', 'Cancelado'
    
    servicio = models.ForeignKey(ServicioIngesta, on_delete=models.CASCADE, related_name='historial')
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, related_name='historial_ingesta')
    
    fecha_inicio = models.DateTimeField(verbose_name="Fecha de inicio")
    fecha_fin = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de finalización")
    duracion_segundos = models.PositiveIntegerField(default=0, verbose_name="Duración (segundos)")
    
    estado = models.CharField(max_length=20, choices=EstadoEjecucion.choices, 
                             default=EstadoEjecucion.EXITOSO, verbose_name="Estado")
    
    correos_procesados = models.PositiveIntegerField(default=0, verbose_name="Correos procesados")
    correos_nuevos = models.PositiveIntegerField(default=0, verbose_name="Correos nuevos")
    archivos_procesados = models.PositiveIntegerField(default=0, verbose_name="Archivos procesados")
    glosas_extraidas = models.PositiveIntegerField(default=0, verbose_name="Glosas extraídas")
    
    mensaje_error = models.TextField(null=True, blank=True, verbose_name="Mensaje de error")
    detalles = models.JSONField(null=True, blank=True, verbose_name="Detalles")
    
    class Meta:
        app_label = 'ingesta_correo'
        verbose_name = "Historial de Ejecución"
        verbose_name_plural = "Historial de Ejecuciones"
        ordering = ['-fecha_inicio']
    
    def __str__(self):
        return f"Ejecución {self.fecha_inicio} - {self.estado}"
    
    def calcular_duracion(self):
        """Calcula la duración de la ejecución."""
        if self.fecha_inicio and self.fecha_fin:
            delta = self.fecha_fin - self.fecha_inicio
            self.duracion_segundos = delta.total_seconds()
            self.save(update_fields=['duracion_segundos'])
        return self.duracion_segundos