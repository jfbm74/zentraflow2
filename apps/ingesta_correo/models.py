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