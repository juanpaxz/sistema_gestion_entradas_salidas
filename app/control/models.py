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
