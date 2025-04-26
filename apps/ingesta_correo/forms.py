from django import forms
from django.core.exceptions import ValidationError
from .models import ReglaFiltrado, CondicionRegla, CategoriaRegla

class ReglaFiltradoForm(forms.ModelForm):
    """
    Formulario para crear y editar reglas de filtrado.
    Permite trabajar tanto con reglas simples como compuestas.
    """
    class Meta:
        model = ReglaFiltrado
        fields = [
            'nombre', 'descripcion', 'categoria', 'activa', 'prioridad',
            'es_compuesta', 'operador_logico', 
            'campo', 'condicion', 'valor',
            'accion', 'parametros_accion',
            'fecha_inicio', 'fecha_fin'
        ]
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'prioridad': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'fecha_inicio': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'fecha_fin': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'parametros_accion': forms.HiddenInput(),
        }
        
    def __init__(self, *args, servicio=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.servicio = servicio
        
        # Si estamos editando una instancia existente, usar su servicio
        if self.instance and self.instance.pk and not servicio:
            self.servicio = self.instance.servicio
            
        # Filtrar categorías por servicio
        if self.servicio:
            self.fields['categoria'].queryset = CategoriaRegla.objects.filter(servicio=self.servicio)
            self.instance.servicio = self.servicio
        
        # Añadir clases a todos los campos
        for field_name, field in self.fields.items():
            if field_name not in ['es_compuesta', 'activa', 'parametros_accion']:
                css_class = field.widget.attrs.get('class', '')
                field.widget.attrs['class'] = f'{css_class} form-control'.strip()
        
        # Personalizar campos específicos
        self.fields['operador_logico'].widget.attrs['class'] = 'form-control regla-compuesta-field'
        self.fields['campo'].widget.attrs['class'] = 'form-control regla-simple-field'
        self.fields['condicion'].widget.attrs['class'] = 'form-control regla-simple-field'
        self.fields['valor'].widget.attrs['class'] = 'form-control regla-simple-field'
        
        # Si es edición y es una regla compuesta, ocultar campos de regla simple
        if self.instance and self.instance.pk and self.instance.es_compuesta:
            self.fields['campo'].widget = forms.HiddenInput()
            self.fields['condicion'].widget = forms.HiddenInput()
            self.fields['valor'].widget = forms.HiddenInput()
            
    def clean(self):
        cleaned_data = super().clean()
        es_compuesta = cleaned_data.get('es_compuesta')
        
        # Validaciones específicas según el tipo de regla
        if es_compuesta:
            # Para reglas compuestas, los campos de regla simple son opcionales
            pass
        else:
            # Para reglas simples, validar campos requeridos
            campo = cleaned_data.get('campo')
            condicion = cleaned_data.get('condicion')
            valor = cleaned_data.get('valor')
            
            if not campo:
                self.add_error('campo', 'Este campo es obligatorio para reglas simples.')
            if not condicion:
                self.add_error('condicion', 'Este campo es obligatorio para reglas simples.')
            if not valor:
                self.add_error('valor', 'Este campo es obligatorio para reglas simples.')
                
        # Validar fechas
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin = cleaned_data.get('fecha_fin')
        
        if fecha_inicio and fecha_fin and fecha_inicio > fecha_fin:
            self.add_error('fecha_fin', 'La fecha de fin debe ser posterior a la fecha de inicio.')
            
        return cleaned_data
    
    def save(self, commit=True):
        regla = super().save(commit=False)
        
        # Asignar servicio si fue proporcionado al formulario
        if self.servicio:
            regla.servicio = self.servicio
            
        if commit:
            regla.save()
            
        return regla


class CondicionReglaForm(forms.ModelForm):
    """
    Formulario para crear y editar condiciones individuales de una regla compuesta.
    """
    class Meta:
        model = CondicionRegla
        fields = ['campo', 'condicion', 'valor', 'orden']
        widgets = {
            'orden': forms.HiddenInput(),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Añadir clases a todos los campos
        for field_name, field in self.fields.items():
            if field_name != 'orden':
                css_class = field.widget.attrs.get('class', '')
                field.widget.attrs['class'] = f'{css_class} form-control'.strip()


class CondicionReglaFormSet(forms.BaseInlineFormSet):
    """
    Formset para manejar múltiples condiciones en una regla compuesta.
    """
    def clean(self):
        super().clean()
        
        # Verificar que hay al menos una condición válida
        valid_forms = [form for form in self.forms if form.is_valid() and form.cleaned_data and not form.cleaned_data.get('DELETE', False)]
        
        if not valid_forms:
            raise ValidationError('Debe añadir al menos una condición para una regla compuesta.')
            
        # Asignar números de orden automáticamente
        for i, form in enumerate(valid_forms):
            form.cleaned_data['orden'] = i
            
    def save_existing(self, form, instance, commit=True):
        """Sobrescribir para asegurar que el orden se guarda correctamente."""
        instance = super().save_existing(form, instance, commit=False)
        if 'orden' in form.cleaned_data:
            instance.orden = form.cleaned_data['orden']
        if commit:
            instance.save()
        return instance
        
    def save_new(self, form, commit=True):
        """Sobrescribir para asegurar que el orden se guarda correctamente."""
        instance = super().save_new(form, commit=False)
        if 'orden' in form.cleaned_data:
            instance.orden = form.cleaned_data['orden']
        if commit:
            instance.save()
        return instance


CondicionReglaInlineFormSet = forms.inlineformset_factory(
    ReglaFiltrado, CondicionRegla, 
    form=CondicionReglaForm,
    formset=CondicionReglaFormSet,
    extra=1, can_delete=True
)


class CategoriaReglaForm(forms.ModelForm):
    """
    Formulario para crear y editar categorías de reglas.
    """
    class Meta:
        model = CategoriaRegla
        fields = ['nombre', 'descripcion', 'color']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
            'color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
        }
        
    def __init__(self, *args, servicio=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.servicio = servicio
        
        # Si estamos editando una instancia existente, usar su servicio
        if self.instance and self.instance.pk and not servicio:
            self.servicio = self.instance.servicio
            
        # Añadir clases a todos los campos
        for field_name, field in self.fields.items():
            css_class = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f'{css_class} form-control'.strip()
            
    def save(self, commit=True):
        categoria = super().save(commit=False)
        
        # Asignar servicio si fue proporcionado al formulario
        if self.servicio:
            categoria.servicio = self.servicio
            
        if commit:
            categoria.save()
            
        return categoria 