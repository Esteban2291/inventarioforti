from django import forms
from .models import Activo, FortiSwitch
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column
from django.forms import inlineformset_factory

# Formulario para Activo
class ActivoForm(forms.ModelForm):
    class Meta:
        model = Activo
        fields = [
            'comando_region', 'titulo_abreviado', 'detalle_unidad',
            'modelo_equipo_fortinet', 'serie_fortinet', 'oblea_fortinet',
            'ospf', 'ip_admin', 'direccion_subred', 'red_dmz', 'red_wifi',
            'grupo_admin_ldap', 'apellido_nombre_admin', 'telefono_admin',
            'observaciones',
        ]
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('comando_region', css_class='form-group col-md-6 mb-0'),
                Column('titulo_abreviado', css_class='form-group col-md-6 mb-0'),
            ),
            Row(Column('detalle_unidad', css_class='form-group col-md-12 mb-0')),
            Row(
                Column('modelo_equipo_fortinet', css_class='form-group col-md-6 mb-0'),
                Column('serie_fortinet', css_class='form-group col-md-6 mb-0'),
            ),
            'oblea_fortinet',
            Row(
                Column('ospf', css_class='form-group col-md-6 mb-0'),
                Column('ip_admin', css_class='form-group col-md-6 mb-0'),
            ),
            Row(
                Column('direccion_subred', css_class='form-group col-md-6 mb-0'),
                Column('red_dmz', css_class='form-group col-md-6 mb-0'),
            ),
            'red_wifi',
            Row(
                Column('grupo_admin_ldap', css_class='form-group col-md-6 mb-0'),
                Column('apellido_nombre_admin', css_class='form-group col-md-6 mb-0'),
            ),
            'telefono_admin',
            'observaciones',
            Submit('submit', 'Guardar Activo', css_class='btn btn-primary mt-3')
        )
# Formulario para FortiSwitch
# core/forms.py
from django import forms
from .models import Activo, FortiSwitch
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column
from django.forms import inlineformset_factory

class ActivoForm(forms.ModelForm):
    # ... (tal como lo tenés)
    pass

class FortiSwitchForm(forms.ModelForm):
    MODELO_CHOICES = [
        ('FortiSwitch 224E', 'FortiSwitch 224E'),
        ('FortiSwitch 248E', 'FortiSwitch 248E'),
    ]

    modelo_equipo = forms.ChoiceField(
        choices=MODELO_CHOICES,
        label='Modelo del Switch',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        self.activo = kwargs.pop('activo', None)  # <- clave para validar por activo
        super().__init__(*args, **kwargs)

    class Meta:
        model = FortiSwitch
        fields = ['modelo_equipo', 'serie', 'oblea']
        widgets = {
            'serie': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'N° de serie'}),
            'oblea': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Oblea (opcional)'}),
        }

    def clean_serie(self):
        serie = (self.cleaned_data.get('serie') or '').strip()
        if self.activo and serie:
            ya_existe = FortiSwitch.objects.filter(activo=self.activo, serie__iexact=serie).exists()
            if ya_existe:
                raise forms.ValidationError("Ya existe un switch con esa serie para este activo.")
        return serie

# FormSet (lo dejás igual)
FortiSwitchFormSet = inlineformset_factory(
    Activo, FortiSwitch, form=FortiSwitchForm, extra=1, can_delete=True
)

class ImportarExcelForm(forms.Form):
    archivo = forms.FileField(label="Seleccionar archivo Excel (.xlsx)")

class CambiarEstadoForm(forms.ModelForm):
    class Meta:
        model = Activo
        fields = ['estado']
        widgets = {'estado': forms.Select(attrs={'class': 'form-select'})}

class LdapLoginForm(forms.Form):
    dni = forms.CharField(label="DNI", max_length=15)
    password = forms.CharField(widget=forms.PasswordInput(), label="Contraseña")

