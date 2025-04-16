from django import forms
from .models import ConfiguracionTenant

class ConfiguracionGeneralForm(forms.ModelForm):
    """Formulario para la configuración general."""
    class Meta:
        model = ConfiguracionTenant
        fields = ['zona_horaria', 'formato_fecha', 'idioma', 'modulo_ingesta', 
                 'modulo_extraccion', 'modulo_flujo', 'modulo_pdf']
    
    clientName = forms.CharField(required=False)
    clientNIT = forms.CharField(required=False)
    eliminar_logo = forms.BooleanField(required=False)
    
class ConfiguracionCorreoForm(forms.ModelForm):
    """Formulario para la configuración de ingesta de correo."""
    class Meta:
        model = ConfiguracionTenant
        fields = ['ingesta_habilitada', 'correo_monitoreo', 'metodo_autenticacion', 
                 'client_id', 'client_secret', 'carpeta_monitoreo', 
                 'intervalo_verificacion', 'marcar_leidos']
    
    reglas_filtro = forms.JSONField(required=False)
    
class ConfiguracionSeguridadForm(forms.ModelForm):
    """Formulario para la configuración de seguridad."""
    class Meta:
        model = ConfiguracionTenant
        fields = ['req_mayusculas', 'req_numeros', 'req_especiales', 
                 'longitud_min_password', 'intentos_bloqueo', 
                 'desbloqueo_automatico', 'metodo_2fa']
    
    rangos_ip = forms.JSONField(required=False)