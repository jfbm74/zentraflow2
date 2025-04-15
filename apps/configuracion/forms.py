# apps/configuracion/forms.py
from django import forms
from apps.tenants.models import Tenant
from apps.core.storage import TenantFileSystemStorage

class TenantConfigForm(forms.Form):
    """Formulario para configuración básica del tenant."""
    name = forms.CharField(max_length=100, required=False)
    nit = forms.CharField(max_length=20, required=False)
    timezone = forms.ChoiceField(
        choices=[
            ('America/Bogota', 'Bogotá (UTC-5)'),
            ('America/Mexico_City', 'Ciudad de México (UTC-6)'),
            ('America/Lima', 'Lima (UTC-5)'),
            ('America/Santiago', 'Santiago (UTC-4)'),
            ('America/Buenos_Aires', 'Buenos Aires (UTC-3)')
        ],
        required=False
    )
    date_format = forms.ChoiceField(
        choices=[
            ('DD/MM/YYYY', 'DD/MM/YYYY'),
            ('MM/DD/YYYY', 'MM/DD/YYYY'),
            ('YYYY-MM-DD', 'YYYY-MM-DD')
        ],
        required=False
    )
    logo = forms.ImageField(required=False)