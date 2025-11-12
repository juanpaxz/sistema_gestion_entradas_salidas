from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Empleado, Asistencia, Justificante
from .models import Horario
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
    horarios = forms.ModelMultipleChoiceField(queryset=Horario.objects.all(), required=False,
                                              widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
                                              help_text='Asignar horarios a este empleado (opcional)')

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'nombre', 'apellido', 'puesto', 'estado', 'rfc', 'huella_biometrica', 'role', 'horarios')

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
        fields = ['nombre', 'apellido', 'puesto', 'estado', 'rfc', 'huella_biometrica', 'horarios']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            css = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = (css + ' form-control').strip()


class JustificanteRetardoForm(forms.ModelForm):
    class Meta:
        model = Justificante
        fields = ['ruta_archivo', 'motivo']
        widgets = {
            'ruta_archivo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'application/pdf',
            }),
            'motivo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Motivo (opcional)'}),
        }
        labels = {
            'ruta_archivo': 'Justificante (PDF)',
            'motivo': 'Motivo'
        }

    def clean_ruta_archivo(self):
        pdf = self.cleaned_data.get('ruta_archivo')
        if pdf:
            # Validar que sea un PDF
            if not pdf.name.lower().endswith('.pdf'):
                raise ValidationError('Solo se aceptan archivos PDF.')
            # Validar tamaño (máximo 10 MB)
            if pdf.size > 10 * 1024 * 1024:
                raise ValidationError('El archivo no puede exceder 10 MB.')
        else:
            raise ValidationError('Debes adjuntar un archivo PDF.')
        return pdf


class HorarioForm(forms.ModelForm):
    # Mostrar días como múltiples opciones para facilitar la creación
    DIAS = [
        ('Lunes', 'Lunes'),
        ('Martes', 'Martes'),
        ('Miércoles', 'Miércoles'),
        ('Jueves', 'Jueves'),
        ('Viernes', 'Viernes'),
        ('Sábado', 'Sábado'),
        ('Domingo', 'Domingo'),
    ]

    dias = forms.MultipleChoiceField(choices=DIAS, widget=forms.CheckboxSelectMultiple, required=True, label='Días laborales')

    class Meta:
        model = Horario
        fields = ['nombre', 'hora_entrada', 'hora_salida']
        widgets = {
            'hora_entrada': forms.TimeInput(format='%H:%M', attrs={'type': 'time', 'class': 'form-control'}),
            'hora_salida': forms.TimeInput(format='%H:%M', attrs={'type': 'time', 'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If editing, populate the 'dias' field from the stored comma-separated value
        if self.instance and self.instance.pk:
            dias_val = self.instance.dias_laborales or ''
            self.fields['dias'].initial = [d.strip() for d in dias_val.split(',') if d.strip()]

    def clean(self):
        cleaned = super().clean()
        dias = cleaned.get('dias')
        if not dias:
            raise forms.ValidationError('Seleccione al menos un día laboral.')
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        dias = self.cleaned_data.get('dias', [])
        instance.dias_laborales = ','.join(dias)
        if commit:
            instance.save()
        return instance
