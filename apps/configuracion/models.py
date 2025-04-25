# Ruta: apps/configuracion/models.py
from django.db import models
from apps.core.storage import TenantFileSystemStorage
import os
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

def tenant_directory_path(instance, filename):
    """
    Ruta donde se almacenará el archivo, estructurada por tenant.
    Ejemplo: 'tenants/tenant_1/logos/logo.png'
    """
    # Asegurarnos de tener solo el nombre del archivo sin ruta
    filename = os.path.basename(filename)
    tenant_id = instance.tenant.id
    
    # Imprimir información de depuración
    print(f"Creando ruta para tenant_id={tenant_id}, filename={filename}")
    path = f'tenants/tenant_{tenant_id}/logos/{filename}'
    print(f"tenant_directory_path: Ruta final: {path}")
    
    return path
class TenantConfig(models.Model):
    """Configuración específica para cada tenant."""
    tenant = models.OneToOneField('tenants.Tenant', on_delete=models.CASCADE, related_name='config')
    timezone = models.CharField(max_length=50, default='America/Bogota')
    date_format = models.CharField(max_length=20, default='DD/MM/YYYY')
    
    # Utilizar el storage personalizado para el logo
    logo = models.ImageField(
        upload_to=tenant_directory_path, 
        storage=TenantFileSystemStorage(),
        null=True, 
        blank=True,
        verbose_name="Logo del cliente"
    )
    
    last_updated = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey('authentication.ZentraflowUser', on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"Configuración para {self.tenant.name}"
    
    class Meta:
        app_label = 'configuracion'  # Sin el prefijo 'apps.'
        verbose_name = "Configuración de Cliente"
        verbose_name_plural = "Configuraciones de Clientes"
        
    def save(self, *args, **kwargs):
        """Asegurar que cada tenant tenga una sola configuración."""
        # Comprobar si ya existe una configuración para este tenant
        if not self.pk:
            existing = TenantConfig.objects.filter(tenant=self.tenant).first()
            if existing:
                # Si ya existe, actualizar en lugar de crear uno nuevo
                self.pk = existing.pk
        super().save(*args, **kwargs)

# apps/configuracion/models.py (añadir al archivo existente)

# apps/configuracion/models.py (fragmento de código para actualizar)

class EmailConfig(models.Model):
    """Modelo para almacenar la configuración de correo por tenant."""
    
    PROTOCOL_CHOICES = [
        ('imap', 'IMAP'),
        ('pop3', 'POP3'),
    ]
    
    tenant = models.OneToOneField('tenants.Tenant', on_delete=models.CASCADE, related_name='email_config')
    email_address = models.EmailField(verbose_name="Dirección de Correo Monitoreada")
    protocol = models.CharField(max_length=4, choices=PROTOCOL_CHOICES, default='imap', verbose_name="Protocolo")
    server_host = models.CharField(max_length=255, verbose_name="Servidor de Correo")
    server_port = models.IntegerField(verbose_name="Puerto", validators=[MinValueValidator(1), MaxValueValidator(65535)])
    username = models.CharField(max_length=255, verbose_name="Usuario")
    password = models.CharField(max_length=255, verbose_name="Contraseña")
    use_ssl = models.BooleanField(default=True, verbose_name="Usar SSL/TLS")
    folder_to_monitor = models.CharField(max_length=100, default="INBOX", verbose_name="Carpeta a Monitorear")
    check_interval = models.IntegerField(
        default=5, 
        verbose_name="Intervalo de Verificación (minutos)",
        validators=[MinValueValidator(1), MaxValueValidator(60)]
    )
    mark_as_read = models.BooleanField(default=True, verbose_name="Marcar como Leído")
    ingesta_enabled = models.BooleanField(default=True, verbose_name="Habilitar Ingesta")
    last_check = models.DateTimeField(null=True, blank=True, verbose_name="Última Verificación")
    connection_status = models.CharField(max_length=50, default="no_verificado", verbose_name="Estado de Conexión")
    connection_error = models.TextField(null=True, blank=True, verbose_name="Error de Conexión")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última Actualización")

    class Meta:
        app_label = 'configuracion'
        verbose_name = "Configuración de Correo"
        verbose_name_plural = "Configuraciones de Correo"
    
    def __str__(self):
        return f"Configuración de correo de {self.email_address} ({self.tenant.name})"
    
    def save(self, *args, **kwargs):
        # Actualizar los puertos por defecto según el protocolo y SSL
        if not self.server_port:
            if self.protocol == 'imap':
                self.server_port = 993 if self.use_ssl else 143
            else:  # pop3
                self.server_port = 995 if self.use_ssl else 110
        
        super().save(*args, **kwargs)
    
    def test_connection(self):
        """Prueba la conexión al servidor de correo."""
        try:
            if self.protocol == 'imap':
                import imaplib
                if self.use_ssl:
                    server = imaplib.IMAP4_SSL(self.server_host, self.server_port)
                else:
                    server = imaplib.IMAP4(self.server_host, self.server_port)
                
                server.login(self.username, self.password)
                server.select(self.folder_to_monitor)
                server.close()
                server.logout()
            else:  # pop3
                import poplib
                if self.use_ssl:
                    server = poplib.POP3_SSL(self.server_host, self.server_port)
                else:
                    server = poplib.POP3(self.server_host, self.server_port)
                
                server.user(self.username)
                server.pass_(self.password)
                server.quit()
            
            self.connection_status = "conectado"
            self.connection_error = None
            self.save()
            return True, "Conexión exitosa"
            
        except Exception as e:
            self.connection_status = "error"
            self.connection_error = str(e)
            self.save()
            return False, f"Error de conexión: {str(e)}"


