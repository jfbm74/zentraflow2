from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _

class CustomUserManager(BaseUserManager):
    """Define un gestor de usuarios personalizado para ZentraflowUser."""
    
    def create_user(self, email, tenant, password=None, **extra_fields):
        """Crea y guarda un usuario con el email y contraseña dados."""
        if not email:
            raise ValueError(_('El Email es obligatorio'))
        email = self.normalize_email(email)
        user = self.model(email=email, tenant=tenant, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, tenant, password=None, **extra_fields):
        """Crea y guarda un superusuario con el email y contraseña dados."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'ADMIN')
        
        return self.create_user(email, tenant, password, **extra_fields)

class ZentraflowUser(AbstractUser):
    """Modelo de usuario personalizado para Zentraflow con soporte multi-tenant."""
    
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', _('Administrador')
        AUDITOR = 'AUDITOR', _('Auditor')
        ANALISTA = 'ANALISTA', _('Analista')
        VISUALIZADOR = 'VISUALIZADOR', _('Visualizador')
    
    # Sobrescribir campos de AbstractUser
    username = None  # No usaremos username, solo email
    email = models.EmailField(_('email address'), unique=True)
    first_name = models.CharField(_('first name'), max_length=150)
    last_name = models.CharField(_('last name'), max_length=150)
    
    # Override ManyToMany relationships to avoid clashes
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name=_('groups'),
        blank=True,
        help_text=_('The groups this user belongs to.'),
        related_name='zentraflow_users',
        related_query_name='zentraflow_user'
    )
    
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name='zentraflow_users_permissions',
        related_query_name='zentraflow_user_permission'
    )
    
    # Campos adicionales
    tenant = models.ForeignKey('apps.tenants.Tenant', on_delete=models.CASCADE, related_name='users', verbose_name="Cliente")
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.VISUALIZADOR, verbose_name="Rol")
    last_login_ip = models.GenericIPAddressField(null=True, blank=True, verbose_name="Última IP")
    failed_login_attempts = models.PositiveSmallIntegerField(default=0, verbose_name="Intentos fallidos")
    is_locked = models.BooleanField(default=False, verbose_name="Bloqueado")
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['tenant']
    
    objects = CustomUserManager()
    
    def __str__(self):
        return f"{self.email} ({self.tenant})"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    class Meta:
        app_label = 'apps.authentication'  # Ensure app_label is correct
        unique_together = ['email', 'tenant']  # Email único por tenant
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"