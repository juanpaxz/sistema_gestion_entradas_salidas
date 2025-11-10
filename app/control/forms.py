from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Empleado
from django.core.exceptions import ValidationError


class EmpleadoCreationForm(UserCreationForm):
    email = forms.EmailField(required=False)
    nombre = forms.CharField(max_length=50)
    apellido = forms.CharField(max_length=50)
    puesto = forms.CharField(max_length=50)
    estado = forms.ChoiceField(
        choices=[('activo', 'Activo'), ('inactivo', 'Inactivo')],
        initial='activo'
    )
    role = forms.ChoiceField(
        choices=[('empleado', 'Empleado'), ('administracion', 'Administrador')],
        initial='empleado',
        label='Rol'
    )
    rfc = forms.CharField(max_length=13)
    huella_biometrica = forms.CharField(max_length=255, required=False)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'nombre', 'apellido', 'puesto', 'estado', 'rfc', 'huella_biometrica', 'role')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add bootstrap classes to widgets
        for name, field in self.fields.items():
            css = field.widget.attrs.get('class', '')
            if name in ('password1', 'password2'):
                field.widget.attrs['class'] = (css + ' form-control').strip()
            else:
                field.widget.attrs['class'] = (css + ' form-control').strip()

    def save(self, commit=True):
        # Create the User first
        user = super().save(commit=False)
        user.email = self.cleaned_data.get('email', '')
        user.first_name = self.cleaned_data.get('nombre', '')
        user.last_name = self.cleaned_data.get('apellido', '')
        if commit:
            user.save()
        # Defer Empleado creation to view to keep responsibilities clear
        return user

    def clean_rfc(self):
        rfc = self.cleaned_data.get('rfc')
        # If an Empleado with this RFC already exists, raise validation error
        if rfc and Empleado.objects.filter(rfc__iexact=rfc).exists():
            raise ValidationError('Ya existe un empleado con ese RFC.')
        return rfc


class EmpleadoForm(forms.ModelForm):
    class Meta:
        model = Empleado
        fields = ['nombre', 'apellido', 'puesto', 'estado', 'rfc', 'huella_biometrica']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            css = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = (css + ' form-control').strip()
