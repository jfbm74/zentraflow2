from django.db import models

class Tenant(models.Model):
    """Modelo para representar a los clientes dentro del sistema multi-tenant."""
    name = models.CharField(max_length=100, unique=True, verbose_name="Nombre")
    domain = models.CharField(max_length=100, unique=True, verbose_name="Dominio")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    is_active = models.BooleanField(default=True, verbose_name="Activo")

    # Campos nuevos
    nit = models.CharField(max_length=20, verbose_name="NIT")
    direccion = models.CharField(max_length=255, verbose_name="Dirección")
    telefono = models.CharField(max_length=20, verbose_name="Teléfono")
    correo_contacto = models.EmailField(max_length=255, verbose_name="Correo de contacto")

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"

    def __str__(self):
        return self.name
