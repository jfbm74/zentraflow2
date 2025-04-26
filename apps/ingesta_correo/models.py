from django.db import models
from django.utils import timezone
from apps.tenants.models import Tenant

# Función para generar la ruta de subida de archivos adjuntos con separación por tenant
def adjunto_upload_path(instance, filename):
    """
    Genera la ruta para guardar los archivos adjuntos organizados por tenant.
    
    Args:
        instance: Instancia de ArchivoAdjunto
        filename: Nombre original del archivo
        
    Returns:
        str: Ruta donde se guardará el archivo
    """
    try:
        # Intentar obtener el tenant desde la instancia
        if instance and hasattr(instance, 'correo') and instance.correo:
            if hasattr(instance.correo, 'servicio') and instance.correo.servicio:
                if hasattr(instance.correo.servicio, 'tenant') and instance.correo.servicio.tenant:
                    tenant_id = instance.correo.servicio.tenant.id
                    # Formato: adjuntos_correo/tenant_id/YYYY/MM/DD/filename
                    return f'adjuntos_correo/tenant_{tenant_id}/{timezone.now().strftime("%Y/%m/%d")}/{filename}'
    except Exception as e:
        # En caso de error, registrar información de diagnóstico
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error al generar ruta para adjunto: {str(e)}")
    
    # Si no se puede obtener el tenant o hay algún error, usar una ruta temporal con timestamp
    # para evitar colisiones
    timestamp = timezone.now().strftime("%Y%m%d%H%M%S")
    return f'adjuntos_correo/temp/{timezone.now().strftime("%Y/%m/%d")}/{timestamp}_{filename}'

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
    archivo = models.FileField(upload_to=adjunto_upload_path, max_length=500)
    procesado = models.BooleanField(default=False)
    fecha_procesamiento = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Archivo Adjunto"
        verbose_name_plural = "Archivos Adjuntos"
    
    def __str__(self):
        return self.nombre_archivo
        
    def save(self, *args, **kwargs):
        """Sobrescribe el método save para garantizar que los archivos se guarden con el tenant en la ruta."""
        # Solo modificar la ruta si el archivo es nuevo y existe la relación completa
        if not self.id and self.correo_id and hasattr(self, 'archivo'):
            try:
                if self.correo.servicio and self.correo.servicio.tenant:
                    # Si el archivo ya se ha asignado pero no guardado aún
                    if hasattr(self.archivo, 'file') and not self.archivo.name.startswith(f'adjuntos_correo/tenant_{self.correo.servicio.tenant.id}'):
                        # Guardar el contenido con la ruta correcta
                        from django.core.files.base import ContentFile
                        tenant_id = self.correo.servicio.tenant.id
                        fecha_actual = timezone.now().strftime("%Y/%m/%d")
                        nombre = self.nombre_archivo
                        ruta_adjunto = f'adjuntos_correo/tenant_{tenant_id}/{fecha_actual}/{nombre}'
                        
                        # Obtener el contenido del archivo actual
                        contenido = self.archivo.read()
                        # Guardar con la nueva ruta
                        self.archivo.save(ruta_adjunto, ContentFile(contenido), save=False)
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error al ajustar ruta de archivo adjunto: {str(e)}")
                
        super().save(*args, **kwargs)

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
        ADJUNTO_TIPO = 'adjunto_tipo', 'Tipo de adjunto'
        ADJUNTO_TAMAÑO = 'adjunto_tamaño', 'Tamaño de adjunto'
        TIENE_ADJUNTOS = 'tiene_adjuntos', 'Tiene adjuntos'
        FECHA_RECEPCION = 'fecha_recepcion', 'Fecha de recepción'
        
    class TipoCondicion(models.TextChoices):
        CONTIENE = 'contiene', 'Contiene'
        NO_CONTIENE = 'no_contiene', 'No contiene'
        ES_IGUAL = 'es_igual', 'Es igual a'
        NO_ES_IGUAL = 'no_es_igual', 'No es igual a'
        EMPIEZA_CON = 'empieza_con', 'Empieza con'
        TERMINA_CON = 'termina_con', 'Termina con'
        REGEX = 'regex', 'Expresión regular'
        MAYOR_QUE = 'mayor_que', 'Mayor que'
        MENOR_QUE = 'menor_que', 'Menor que'
        ENTRE = 'entre', 'Entre valores'
        ES_VERDADERO = 'es_verdadero', 'Es verdadero'
        ES_FALSO = 'es_falso', 'Es falso'
        
    class TipoAccion(models.TextChoices):
        PROCESAR = 'procesar', 'Procesar correo'
        IGNORAR = 'ignorar', 'Ignorar correo'
        MARCAR_REVISION = 'marcar_revision', 'Marcar para revisión'
        ETIQUETAR = 'etiquetar', 'Etiquetar correo'
        PRIORIDAD_ALTA = 'prioridad_alta', 'Asignar prioridad alta'
        PRIORIDAD_MEDIA = 'prioridad_media', 'Asignar prioridad media'
        PRIORIDAD_BAJA = 'prioridad_baja', 'Asignar prioridad baja'
        NOTIFICAR = 'notificar', 'Enviar notificación'
        
    class TipoOperador(models.TextChoices):
        """Tipo de operador lógico para grupos de condiciones."""
        Y = 'AND', 'Todas las condiciones deben cumplirse (Y)'
        O = 'OR', 'Al menos una condición debe cumplirse (O)'
        
    servicio = models.ForeignKey(ServicioIngesta, on_delete=models.CASCADE, related_name='reglas')
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(null=True, blank=True, help_text="Descripción detallada de la regla")
    # Para reglas simples, estos campos siguen funcionando
    campo = models.CharField(max_length=20, choices=TipoCampo.choices, null=True, blank=True)
    condicion = models.CharField(max_length=20, choices=TipoCondicion.choices, null=True, blank=True)
    valor = models.CharField(max_length=255, null=True, blank=True)
    # Para reglas compuestas, se usará el grupo de condiciones
    es_compuesta = models.BooleanField(default=False, help_text="Indica si la regla usa múltiples condiciones")
    operador_logico = models.CharField(max_length=3, choices=TipoOperador.choices, default=TipoOperador.Y)
    # Acción a ejecutar
    accion = models.CharField(max_length=20, choices=TipoAccion.choices)
    parametros_accion = models.JSONField(null=True, blank=True, help_text="Parámetros adicionales para la acción")
    # Metadatos
    activa = models.BooleanField(default=True)
    prioridad = models.IntegerField(default=0)
    fecha_inicio = models.DateTimeField(null=True, blank=True, help_text="Fecha desde la que la regla está activa")
    fecha_fin = models.DateTimeField(null=True, blank=True, help_text="Fecha hasta la que la regla está activa")
    conteo_usos = models.IntegerField(default=0, help_text="Número de veces que la regla ha sido aplicada")
    ultima_aplicacion = models.DateTimeField(null=True, blank=True, help_text="Última vez que la regla fue aplicada")
    # Auditoría
    creado_en = models.DateTimeField(auto_now_add=True)
    modificado_en = models.DateTimeField(auto_now=True)
    creado_por = models.ForeignKey('authentication.ZentraflowUser', related_name='reglas_creadas', 
                                 on_delete=models.SET_NULL, null=True, blank=True)
    modificado_por = models.ForeignKey('authentication.ZentraflowUser', related_name='reglas_modificadas', 
                                     on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name = "Regla de Filtrado"
        verbose_name_plural = "Reglas de Filtrado"
        ordering = ['prioridad', 'nombre']
        
    def __str__(self):
        if self.es_compuesta:
            return f"{self.nombre} (Regla compuesta)"
        return f"{self.nombre} ({self.get_campo_display()} {self.get_condicion_display()} '{self.valor}')"
    
    def evaluar(self, correo):
        """
        Evalúa la regla contra un correo específico.
        
        Args:
            correo: Un objeto CorreoIngesta a evaluar
            
        Returns:
            bool: True si la regla se cumple, False en caso contrario
        """
        if self.es_compuesta:
            # Evaluar grupo de condiciones
            condiciones = self.condiciones.all()
            if not condiciones:
                return False
                
            if self.operador_logico == self.TipoOperador.Y:
                # Todas deben cumplirse
                return all(condicion.evaluar(correo) for condicion in condiciones)
            else:
                # Al menos una debe cumplirse
                return any(condicion.evaluar(correo) for condicion in condiciones)
        else:
            # Regla simple (retrocompatible)
            return self._evaluar_condicion_simple(correo)
            
    def _evaluar_condicion_simple(self, correo):
        """Evalúa una condición simple en un correo."""
        valor_campo = self._obtener_valor_campo(correo, self.campo)
        
        # Convertir condición a mayúsculas para hacer la comparación insensible a mayúsculas/minúsculas
        condicion_upper = self.condicion.upper() if self.condicion else ""
        
        # Convertir a minúsculas para comparaciones insensibles a mayúsculas/minúsculas
        valor_campo_lower = valor_campo.lower()
        valor_lower = self.valor.lower() if self.valor else ""
        
        # Evaluar según tipo de condición
        if condicion_upper == self.TipoCondicion.CONTIENE.upper():
            return valor_lower in valor_campo_lower
        elif condicion_upper == self.TipoCondicion.NO_CONTIENE.upper():
            return valor_lower not in valor_campo_lower
        elif condicion_upper == self.TipoCondicion.ES_IGUAL.upper():
            return valor_lower == valor_campo_lower
        elif condicion_upper == self.TipoCondicion.NO_ES_IGUAL.upper():
            return valor_lower != valor_campo_lower
        elif condicion_upper == self.TipoCondicion.EMPIEZA_CON.upper():
            return valor_campo_lower.startswith(valor_lower)
        elif condicion_upper == self.TipoCondicion.TERMINA_CON.upper():
            return valor_campo_lower.endswith(valor_lower)
        elif condicion_upper == self.TipoCondicion.REGEX.upper():
            import re
            try:
                return bool(re.search(self.valor, valor_campo, re.IGNORECASE))
            except re.error:
                return False
        
        return False
        
    def _obtener_valor_campo(self, correo, campo):
        """Obtiene el valor del campo especificado de un correo."""
        # Convertir campo a mayúsculas para hacer la comparación insensible a mayúsculas/minúsculas
        campo_upper = campo.upper() if campo else ""
        
        if campo_upper == self.TipoCampo.REMITENTE.upper():
            return correo.remitente
        elif campo_upper == self.TipoCampo.ASUNTO.upper():
            return correo.asunto
        elif campo_upper == self.TipoCampo.CONTENIDO.upper():
            return correo.contenido_plano or ""
        elif campo_upper == self.TipoCampo.ADJUNTO_NOMBRE.upper():
            # Concatenar todos los nombres de adjuntos
            return " ".join([adj.nombre_archivo for adj in correo.adjuntos.all()])
        elif campo_upper == self.TipoCampo.TIENE_ADJUNTOS.upper():
            return str(correo.adjuntos.exists())
        elif campo_upper == self.TipoCampo.ADJUNTO_TIPO.upper():
            return " ".join([adj.tipo_contenido for adj in correo.adjuntos.all()])
        elif campo_upper == self.TipoCampo.ADJUNTO_TAMAÑO.upper():
            # Tamaño total de los adjuntos en KB
            return str(sum([adj.tamaño for adj in correo.adjuntos.all()]) / 1024)
        elif campo_upper == self.TipoCampo.FECHA_RECEPCION.upper():
            return correo.fecha_recepcion.strftime('%Y-%m-%d %H:%M:%S')
        return ""
        
    def registrar_uso(self):
        """Registra que la regla ha sido aplicada."""
        self.conteo_usos += 1
        self.ultima_aplicacion = timezone.now()
        self.save(update_fields=['conteo_usos', 'ultima_aplicacion'])
        
    def esta_activa(self):
        """Verifica si la regla está activa considerando fechas de inicio/fin."""
        if not self.activa:
            return False
            
        ahora = timezone.now()
        if self.fecha_inicio and ahora < self.fecha_inicio:
            return False
            
        if self.fecha_fin and ahora > self.fecha_fin:
            return False
            
        return True
        
    def ejecutar_accion(self, correo):
        """
        Ejecuta la acción definida por la regla sobre un correo.
        
        Args:
            correo: Objeto CorreoIngesta sobre el que se ejecutará la acción
            
        Returns:
            bool: True si la acción se ejecutó correctamente
        """
        self.registrar_uso()
        
        if self.accion == self.TipoAccion.PROCESAR:
            # Marcar para procesamiento
            correo.estado = CorreoIngesta.Estado.PENDIENTE
        elif self.accion == self.TipoAccion.IGNORAR:
            # Marcar como ignorado con un estado especial
            correo.estado = "IGNORADO"
        elif self.accion == self.TipoAccion.MARCAR_REVISION:
            # Marcar para revisión manual
            correo.estado = "REVISION"
        elif self.accion == self.TipoAccion.ETIQUETAR:
            # Etiquetar el correo (se guarda en JSON field)
            etiquetas = correo.detalles.get('etiquetas', []) if correo.detalles else []
            nueva_etiqueta = self.parametros_accion.get('etiqueta', 'sin_etiqueta')
            if nueva_etiqueta not in etiquetas:
                etiquetas.append(nueva_etiqueta)
                
            if not correo.detalles:
                correo.detalles = {}
            correo.detalles['etiquetas'] = etiquetas
        
        # Guardar cambios en el correo
        correo.save()
        return True


class CondicionRegla(models.Model):
    """
    Representa una condición individual dentro de una regla compuesta.
    Cada regla compuesta puede tener múltiples condiciones conectadas por operadores lógicos.
    """
    regla = models.ForeignKey(ReglaFiltrado, on_delete=models.CASCADE, related_name='condiciones')
    campo = models.CharField(max_length=20, choices=ReglaFiltrado.TipoCampo.choices)
    condicion = models.CharField(max_length=20, choices=ReglaFiltrado.TipoCondicion.choices)
    valor = models.CharField(max_length=255)
    orden = models.PositiveSmallIntegerField(default=0, help_text="Orden de evaluación dentro de la regla")
    
    class Meta:
        verbose_name = "Condición"
        verbose_name_plural = "Condiciones"
        ordering = ['regla', 'orden']
        
    def __str__(self):
        return f"{self.get_campo_display()} {self.get_condicion_display()} '{self.valor}'"
        
    def evaluar(self, correo):
        """Evalúa esta condición contra un correo específico."""
        valor_campo = self._obtener_valor_campo(correo, self.campo)
        
        # Convertir condición a mayúsculas para hacer la comparación insensible a mayúsculas/minúsculas
        condicion_upper = self.condicion.upper() if self.condicion else ""
        
        # Evaluar según tipo de condición
        if condicion_upper == ReglaFiltrado.TipoCondicion.CONTIENE.upper():
            return self.valor in valor_campo
        elif condicion_upper == ReglaFiltrado.TipoCondicion.NO_CONTIENE.upper():
            return self.valor not in valor_campo
        elif condicion_upper == ReglaFiltrado.TipoCondicion.ES_IGUAL.upper():
            return self.valor == valor_campo
        elif condicion_upper == ReglaFiltrado.TipoCondicion.NO_ES_IGUAL.upper():
            return self.valor != valor_campo
        elif condicion_upper == ReglaFiltrado.TipoCondicion.EMPIEZA_CON.upper():
            return valor_campo.startswith(self.valor)
        elif condicion_upper == ReglaFiltrado.TipoCondicion.TERMINA_CON.upper():
            return valor_campo.endswith(self.valor)
        elif condicion_upper == ReglaFiltrado.TipoCondicion.REGEX.upper():
            import re
            try:
                return bool(re.search(self.valor, valor_campo))
            except re.error:
                return False
        elif condicion_upper == ReglaFiltrado.TipoCondicion.MAYOR_QUE.upper():
            try:
                return float(valor_campo) > float(self.valor)
            except (ValueError, TypeError):
                return False
        elif condicion_upper == ReglaFiltrado.TipoCondicion.MENOR_QUE.upper():
            try:
                return float(valor_campo) < float(self.valor)
            except (ValueError, TypeError):
                return False
        elif condicion_upper == ReglaFiltrado.TipoCondicion.ES_VERDADERO.upper():
            return valor_campo.lower() in ('true', 'verdadero', 'si', 'yes', '1')
        elif condicion_upper == ReglaFiltrado.TipoCondicion.ES_FALSO.upper():
            return valor_campo.lower() in ('false', 'falso', 'no', '0')
        
        return False
        
    def _obtener_valor_campo(self, correo, campo):
        """Obtiene el valor del campo especificado de un correo."""
        # Convertir campo a mayúsculas para hacer la comparación insensible a mayúsculas/minúsculas
        campo_upper = campo.upper() if campo else ""
        
        if campo_upper == self.TipoCampo.REMITENTE.upper():
            return correo.remitente
        elif campo_upper == self.TipoCampo.ASUNTO.upper():
            return correo.asunto
        elif campo_upper == self.TipoCampo.CONTENIDO.upper():
            return correo.contenido_plano or ""
        elif campo_upper == self.TipoCampo.ADJUNTO_NOMBRE.upper():
            # Concatenar todos los nombres de adjuntos
            return " ".join([adj.nombre_archivo for adj in correo.adjuntos.all()])
        elif campo_upper == self.TipoCampo.TIENE_ADJUNTOS.upper():
            return str(correo.adjuntos.exists())
        elif campo_upper == self.TipoCampo.ADJUNTO_TIPO.upper():
            return " ".join([adj.tipo_contenido for adj in correo.adjuntos.all()])
        elif campo_upper == self.TipoCampo.ADJUNTO_TAMAÑO.upper():
            # Tamaño total de los adjuntos en KB
            return str(sum([adj.tamaño for adj in correo.adjuntos.all()]) / 1024)
        elif campo_upper == self.TipoCampo.FECHA_RECEPCION.upper():
            return correo.fecha_recepcion.strftime('%Y-%m-%d %H:%M:%S')
        return ""


class HistorialAplicacionRegla(models.Model):
    """
    Registra cuándo y cómo se aplicó una regla a un correo específico.
    Esto permite auditoría y análisis de la efectividad de las reglas.
    """
    regla = models.ForeignKey(ReglaFiltrado, on_delete=models.CASCADE, related_name='historial')
    correo = models.ForeignKey(CorreoIngesta, on_delete=models.CASCADE, related_name='reglas_aplicadas')
    fecha_aplicacion = models.DateTimeField(auto_now_add=True)
    resultado = models.BooleanField(help_text="True si la regla se cumplió, False si no")
    accion_ejecutada = models.CharField(max_length=100, null=True, blank=True)
    detalles = models.JSONField(null=True, blank=True, help_text="Detalles adicionales de la evaluación")
    
    class Meta:
        verbose_name = "Historial de Aplicación de Regla"
        verbose_name_plural = "Historial de Aplicación de Reglas"
        ordering = ['-fecha_aplicacion']
        indexes = [
            models.Index(fields=['regla', 'fecha_aplicacion']),
            models.Index(fields=['correo', 'fecha_aplicacion']),
        ]
        
    def __str__(self):
        return f"Regla '{self.regla}' aplicada a correo {self.correo.id}"


class CategoriaRegla(models.Model):
    """
    Permite agrupar reglas por categorías para mejor organización.
    """
    servicio = models.ForeignKey(ServicioIngesta, on_delete=models.CASCADE, related_name='categorias_reglas')
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(null=True, blank=True)
    color = models.CharField(max_length=7, default="#3498db", help_text="Color hexadecimal para identificar la categoría")
    
    class Meta:
        verbose_name = "Categoría de Reglas"
        verbose_name_plural = "Categorías de Reglas"
        ordering = ['nombre']
        unique_together = ('servicio', 'nombre')
        
    def __str__(self):
        return self.nombre


class RegistroLogRegla(models.Model):
    """
    Registro detallado de la evaluación de reglas de filtrado.
    Permite un seguimiento paso a paso del proceso de evaluación
    de cada regla contra cada correo.
    """
    class TipoLog(models.TextChoices):
        INFO = 'INFO', 'Información'
        DEBUG = 'DEBUG', 'Depuración'
        WARNING = 'WARNING', 'Advertencia'
        ERROR = 'ERROR', 'Error'
        TRACE = 'TRACE', 'Traza'
    
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    regla = models.ForeignKey(ReglaFiltrado, on_delete=models.CASCADE, related_name='logs_evaluacion',
                             null=True, blank=True)
    correo = models.ForeignKey(CorreoIngesta, on_delete=models.CASCADE, related_name='logs_evaluacion',
                              null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    nivel = models.CharField(max_length=10, choices=TipoLog.choices, default=TipoLog.INFO)
    mensaje = models.TextField()
    datos_contexto = models.JSONField(null=True, blank=True, 
                                    help_text="Datos adicionales relacionados con el evento de evaluación")
    
    class Meta:
        verbose_name = "Registro de Log de Regla"
        verbose_name_plural = "Registros de Log de Reglas"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['tenant', 'timestamp']),
            models.Index(fields=['regla', 'timestamp']),
            models.Index(fields=['correo', 'timestamp']),
            models.Index(fields=['nivel', 'timestamp']),
        ]
        
    def __str__(self):
        return f"[{self.nivel}] {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')} - {self.mensaje[:50]}..."
    
    @classmethod
    def log(cls, tenant, nivel, mensaje, regla=None, correo=None, datos_contexto=None):
        """
        Método de ayuda para crear entradas de log fácilmente.
        
        Args:
            tenant: Tenant relacionado
            nivel: Nivel de log (INFO, DEBUG, WARNING, ERROR, TRACE)
            mensaje: Mensaje descriptivo
            regla: Objeto ReglaFiltrado opcional
            correo: Objeto CorreoIngesta opcional
            datos_contexto: Diccionario con datos de contexto adicionales
            
        Returns:
            RegistroLogRegla: El objeto de registro creado
        """
        return cls.objects.create(
            tenant=tenant,
            nivel=nivel,
            mensaje=mensaje,
            regla=regla,
            correo=correo,
            datos_contexto=datos_contexto
        )


# Añadimos relación de categoría a las reglas
ReglaFiltrado.add_to_class('categoria', 
                           models.ForeignKey(CategoriaRegla, 
                                            on_delete=models.SET_NULL, 
                                            null=True, blank=True, 
                                            related_name='reglas')) 