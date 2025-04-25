from django.db import models
from django.utils import timezone
from apps.tenants.models import Tenant

class ServicioIngesta(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(null=True, blank=True)
    activo = models.BooleanField(default=True)
    ultima_ejecucion = models.DateTimeField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    modificado_por = models.ForeignKey('authentication.ZentraflowUser', on_delete=models.SET_NULL, null=True, blank=True)
    intervalo_minutos = models.IntegerField(default=5)
    proxima_ejecucion = models.DateTimeField(null=True, blank=True)
    en_ejecucion = models.BooleanField(default=False)
    ultima_verificacion = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Servicio de Ingesta"
        verbose_name_plural = "Servicios de Ingesta"
        unique_together = ('tenant', 'nombre')

    def __str__(self):
        return f"{self.nombre} - {self.tenant}"

    def actualizar_proxima_ejecucion(self):
        """Actualiza el timestamp de próxima ejecución basado en el intervalo."""
        self.proxima_ejecucion = timezone.now() + timezone.timedelta(minutes=self.intervalo_minutos)
        return self.proxima_ejecucion

    def tiempo_hasta_proxima_ejecucion(self):
        """Calcula el tiempo hasta la próxima ejecución y lo devuelve en formato legible."""
        if not self.proxima_ejecucion:
            return "No programado"
            
        if not self.activo:
            return "Servicio inactivo"
            
        now = timezone.now()
        if self.proxima_ejecucion <= now:
            return "Pendiente"
            
        # Calcular diferencia de tiempo
        delta = self.proxima_ejecucion - now
        seconds = delta.total_seconds()
        
        # Formatear tiempo
        if seconds < 60:
            return f"{int(seconds)} segundos"
        elif seconds < 3600:
            return f"{int(seconds/60)} minutos"
        elif seconds < 86400:
            horas = int(seconds/3600)
            minutos = int((seconds % 3600) / 60)
            return f"{horas} horas, {minutos} minutos"
        else:
            dias = int(seconds/86400)
            horas = int((seconds % 86400) / 3600)
            return f"{dias} días, {horas} horas"

    @property
    def correos_procesados_total(self):
        """Retorna el total de correos procesados por este servicio."""
        from django.db.models import Sum
        return self.historial.aggregate(total=Sum('correos_procesados'))['total'] or 0
        
    @property
    def correos_ultima_ejecucion(self):
        """Retorna el número de correos procesados en la última ejecución."""
        ultima = self.historial.order_by('-fecha_inicio').first()
        return ultima.correos_procesados if ultima else 0

class HistorialEjecucion(models.Model):
    class EstadoEjecucion(models.TextChoices):
        EN_PROCESO = 'en_proceso', 'En Proceso'
        EXITOSO = 'exitoso', 'Exitoso'
        ERROR = 'error', 'Error'
        PARCIAL = 'parcial', 'Parcial'
        CANCELADO = 'cancelado', 'Cancelado'

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    servicio = models.ForeignKey(ServicioIngesta, on_delete=models.CASCADE, related_name='historial')
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(
        max_length=20,
        choices=EstadoEjecucion.choices,
        default=EstadoEjecucion.EN_PROCESO
    )
    correos_procesados = models.IntegerField(default=0)
    correos_nuevos = models.IntegerField(default=0)
    archivos_procesados = models.IntegerField(default=0)
    glosas_extraidas = models.IntegerField(default=0)
    mensaje_error = models.TextField(null=True, blank=True)
    detalles = models.JSONField(null=True, blank=True)

    class Meta:
        verbose_name = "Historial de Ejecución"
        verbose_name_plural = "Historiales de Ejecución"
        ordering = ['-fecha_inicio']

    def __str__(self):
        return f"{self.servicio} - {self.fecha_inicio}"

    @property
    def duracion_segundos(self):
        if self.fecha_fin and self.fecha_inicio:
            return (self.fecha_fin - self.fecha_inicio).total_seconds()
        return None

class CorreoIngesta(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = 'PENDIENTE', 'Pendiente'
        PROCESADO = 'PROCESADO', 'Procesado'
        ERROR = 'ERROR', 'Error'
    
    servicio = models.ForeignKey(ServicioIngesta, on_delete=models.CASCADE, related_name='correos')
    mensaje_id = models.CharField(max_length=255, unique=True)
    remitente = models.CharField(max_length=255)
    destinatarios = models.TextField()
    asunto = models.CharField(max_length=500)
    fecha_recepcion = models.DateTimeField()
    fecha_procesamiento = models.DateTimeField(null=True, blank=True)
    contenido_plano = models.TextField(null=True, blank=True)
    contenido_html = models.TextField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PENDIENTE)
    error = models.TextField(null=True, blank=True)
    glosas_extraidas = models.IntegerField(default=0)
    
    class Meta:
        verbose_name = "Correo"
        verbose_name_plural = "Correos"
        ordering = ['-fecha_recepcion']
    
    def __str__(self):
        return f"{self.asunto} - {self.fecha_recepcion}"

class ArchivoAdjunto(models.Model):
    correo = models.ForeignKey(CorreoIngesta, on_delete=models.CASCADE, related_name='adjuntos')
    nombre_archivo = models.CharField(max_length=255)
    tipo_contenido = models.CharField(max_length=100)
    tamaño = models.IntegerField()
    archivo = models.FileField(upload_to='adjuntos_correo/%Y/%m/%d/', max_length=500)
    procesado = models.BooleanField(default=False)
    fecha_procesamiento = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Archivo Adjunto"
        verbose_name_plural = "Archivos Adjuntos"
    
    def __str__(self):
        return self.nombre_archivo

class LogActividad(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    fecha_hora = models.DateTimeField(default=timezone.now)
    evento = models.CharField(max_length=100)
    detalles = models.TextField(null=True, blank=True)
    usuario = models.ForeignKey('authentication.ZentraflowUser', on_delete=models.SET_NULL, null=True, blank=True)
    estado = models.CharField(max_length=100, default='info')
    
    class Meta:
        verbose_name = "Log de Actividad"
        verbose_name_plural = "Logs de Actividad"
        ordering = ['-fecha_hora']
    
    def __str__(self):
        return f"{self.evento} - {self.fecha_hora}"

class EstadisticaDiaria(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    fecha = models.DateField()
    correos_procesados = models.IntegerField(default=0)
    glosas_extraidas = models.IntegerField(default=0)
    pendientes = models.IntegerField(default=0)
    errores = models.IntegerField(default=0)
    
    class Meta:
        verbose_name = "Estadística Diaria"
        verbose_name_plural = "Estadísticas Diarias"
        unique_together = ('tenant', 'fecha')
    
    def __str__(self):
        return f"Estadísticas {self.tenant} - {self.fecha}" 

class ReglaFiltrado(models.Model):
    """
    Modelo para reglas de filtrado de correos.
    Permite definir condiciones para procesar o ignorar correos basado en distintos criterios.
    """
    class TipoCampo(models.TextChoices):
        REMITENTE = 'remitente', 'Remitente'
        ASUNTO = 'asunto', 'Asunto'
        CONTENIDO = 'contenido', 'Contenido del correo'
        ADJUNTO_NOMBRE = 'adjunto_nombre', 'Nombre de adjunto'
        
    class TipoCondicion(models.TextChoices):
        CONTIENE = 'contiene', 'Contiene'
        NO_CONTIENE = 'no_contiene', 'No contiene'
        ES_IGUAL = 'es_igual', 'Es igual a'
        EMPIEZA_CON = 'empieza_con', 'Empieza con'
        TERMINA_CON = 'termina_con', 'Termina con'
        REGEX = 'regex', 'Expresión regular'
        
    class TipoAccion(models.TextChoices):
        PROCESAR = 'procesar', 'Procesar correo'
        IGNORAR = 'ignorar', 'Ignorar correo'
        MARCAR_REVISION = 'marcar_revision', 'Marcar para revisión'
        
    servicio = models.ForeignKey(ServicioIngesta, on_delete=models.CASCADE, related_name='reglas')
    nombre = models.CharField(max_length=100)
    campo = models.CharField(max_length=20, choices=TipoCampo.choices)
    condicion = models.CharField(max_length=20, choices=TipoCondicion.choices)
    valor = models.CharField(max_length=255)
    accion = models.CharField(max_length=20, choices=TipoAccion.choices)
    activa = models.BooleanField(default=True)
    prioridad = models.IntegerField(default=0)
    creado_en = models.DateTimeField(auto_now_add=True)
    modificado_en = models.DateTimeField(auto_now=True)
    creado_por = models.ForeignKey('authentication.ZentraflowUser', on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name = "Regla de Filtrado"
        verbose_name_plural = "Reglas de Filtrado"
        ordering = ['prioridad', 'nombre']
        
    def __str__(self):
        return f"{self.nombre} ({self.get_campo_display()} {self.get_condicion_display()} '{self.valor}')" 