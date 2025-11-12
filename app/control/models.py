from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Empleado(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=50)
    apellido = models.CharField(max_length=50)
    puesto = models.CharField(max_length=50)
    huella_biometrica = models.CharField(max_length=255, null=True, blank=True)
    estado = models.CharField(
        max_length=20,
        choices=[('activo', 'Activo'), ('inactivo', 'Inactivo')],
        default='activo'
    )
    rfc = models.CharField(max_length=13, unique=True)
    # Horarios asignados al empleado (muchos a muchos -> un horario puede asignarse a varios empleados)
    horarios = models.ManyToManyField('Horario', blank=True, related_name='empleados')

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

class Asistencia(models.Model):
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name='asistencias')
    fecha = models.DateField(default=timezone.now)
    hora_entrada = models.DateTimeField(null=True, blank=True)
    hora_salida = models.DateTimeField(null=True, blank=True)
    
    TIPO_CHOICES = [
        ('normal', 'Normal'),
        ('retardo', 'Retardo'),
        ('falta', 'Falta'),
        ('justificada', 'Falta Justificada'),
    ]
    
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='normal')
    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ['empleado', 'fecha']
        ordering = ['-fecha', '-hora_entrada']

    def __str__(self):
        return f"{self.empleado} - {self.fecha}"

    def registrar_entrada(self):
        if not self.hora_entrada:
            self.hora_entrada = timezone.now()
            self.save()

    def registrar_salida(self):
        if self.hora_entrada and not self.hora_salida:
            self.hora_salida = timezone.now()
            self.save()


class Justificante(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
    ]

    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name='justificantes')
    asistencia = models.ForeignKey(Asistencia, on_delete=models.CASCADE, related_name='justificantes')
    fecha_envio = models.DateTimeField(auto_now_add=True)
    motivo = models.CharField(max_length=255, blank=True, null=True)
    archivo_url = models.URLField(blank=True, null=True, help_text='URL opcional del justificante')
    ruta_archivo = models.FileField(upload_to='justificantes/', blank=True, null=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    observacion = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-fecha_envio']

    def __str__(self):
        return f"Justificante {self.pk} - {self.empleado} - {self.asistencia.fecha} ({self.estado})"


class Horario(models.Model):
    """Modelo para definir horarios de trabajo reutilizables.

    - dias_laborales: se guarda como cadena separada por comas (p.ej. 'Lunes,Martes')
    - hora_entrada / hora_salida: horarios del día (TimeField)
    """
    DIAS_CHOICES = [
        ('Lunes', 'Lunes'),
        ('Martes', 'Martes'),
        ('Miércoles', 'Miércoles'),
        ('Jueves', 'Jueves'),
        ('Viernes', 'Viernes'),
        ('Sábado', 'Sábado'),
        ('Domingo', 'Domingo'),
    ]

    nombre = models.CharField(max_length=100, blank=True, null=True, help_text='Nombre opcional para identificar el horario')
    dias_laborales = models.CharField(max_length=100, help_text='Días laborales separados por comas (p.ej. Lunes,Martes)')
    hora_entrada = models.TimeField()
    hora_salida = models.TimeField()

    def __str__(self):
        if self.nombre:
            return f"{self.nombre} ({self.dias_laborales})"
        return f"Horario {self.pk} ({self.dias_laborales})"
