from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import datetime

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

    def get_horario_para_fecha(self, fecha=None):
        """
        Devuelve el objeto Horario aplicable para la fecha dada (por defecto hoy).
        Busca entre los horarios asignados al empleado aquel(s) que contienen
        el día de la semana en su campo `dias_laborales` (cadena separada por comas).
        Si hay varios, devuelve el que tenga la hora_entrada más temprana.
        Si no hay ninguno, devuelve None.
        """
        from datetime import date as _date

        if fecha is None:
            fecha = _date.today()

        # Mapear weekday() (0=Lunes) a nombres en español usados en dias_laborales
        weekday_map = {
            0: 'Lunes', 1: 'Martes', 2: 'Miércoles', 3: 'Jueves', 4: 'Viernes', 5: 'Sábado', 6: 'Domingo'
        }
        nombre_dia = weekday_map[fecha.weekday()]

        candidatos = []
        for h in self.horarios.all():
            # dias_laborales se espera como 'Lunes,Martes' etc.
            dias = [d.strip() for d in (h.dias_laborales or '').split(',') if d.strip()]
            if nombre_dia in dias:
                candidatos.append(h)

        if not candidatos:
            return None

        # devolver horario con hora_entrada mínima (por si hay varios)
        return min(candidatos, key=lambda x: x.hora_entrada)

class Asistencia(models.Model):
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name='asistencias')
    fecha = models.DateField(default=timezone.now)
    hora_entrada = models.TimeField(null=True, blank=True)
    hora_salida = models.TimeField(null=True, blank=True)
        
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
            # Guardar solo la hora (TimeField) en la zona local
            now = timezone.localtime(timezone.now())
            self.hora_entrada = now.time()
            self.save()

    def registrar_salida(self):
        if self.hora_entrada and not self.hora_salida:
            now = timezone.localtime(timezone.now())
            self.hora_salida = now.time()
            self.save()

    @property
    def diferencia(self):
        if not self.hora_entrada:
            return None

        # obtener horario aplicable
        try:
            horario = self.empleado.get_horario_para_fecha(self.fecha)
        except Exception:
            horario = None

        if not horario or not horario.hora_entrada:
            return None

        # hora programada (TimeField en Horario)
        h_prog = horario.hora_entrada
        if isinstance(h_prog, datetime.datetime):
            h_prog = h_prog.time()
        if not isinstance(h_prog, datetime.time):
            return None

        # Construir datetimes aware para comparar
        try:
            prog_naive = datetime.datetime.combine(self.fecha, h_prog)
            prog_aware = timezone.make_aware(prog_naive, timezone.get_current_timezone())
        except Exception:
            return None

        # Determinar datetime de entrada a partir del campo (puede ser time o datetime)
        entrada_dt = None
        if isinstance(self.hora_entrada, datetime.time):
            try:
                ent_naive = datetime.datetime.combine(self.fecha, self.hora_entrada)
                entrada_dt = timezone.make_aware(ent_naive, timezone.get_current_timezone())
            except Exception:
                return None
        elif isinstance(self.hora_entrada, datetime.datetime):
            entrada_dt = self.hora_entrada
            if timezone.is_naive(entrada_dt):
                try:
                    entrada_dt = timezone.make_aware(entrada_dt, timezone.get_current_timezone())
                except Exception:
                    pass
        else:
            return None

        # Calcular diferencia en segundos
        try:
            diff_seconds = (entrada_dt - prog_aware).total_seconds()
        except Exception:
            return None

        # puntual
        if abs(diff_seconds) < 60:
            return "A tiempo"

        mins = abs(int(diff_seconds // 60))
        return f"{mins} min tarde" if diff_seconds > 0 else f"{mins} min antes"

    def compute_diferencia_minutes(self):
        if not self.hora_entrada:
            return None

        try:
            horario = self.empleado.get_horario_para_fecha(self.fecha)
        except Exception:
            return None

        if not horario or not horario.hora_entrada:
            return None

        h_prog = horario.hora_entrada
        if isinstance(h_prog, datetime.datetime):
            h_prog = h_prog.time()

        try:
            prog_naive = datetime.datetime.combine(self.fecha, h_prog)
            prog_aware = timezone.make_aware(prog_naive, timezone.get_current_timezone())
        except Exception:
            return None

        # normalización
        if isinstance(self.hora_entrada, datetime.time):
            ent_naive = datetime.datetime.combine(self.fecha, self.hora_entrada)
            entrada_dt = timezone.make_aware(ent_naive, timezone.get_current_timezone())
        else:
            entrada_dt = self.hora_entrada
            if timezone.is_naive(entrada_dt):
                entrada_dt = timezone.make_aware(entrada_dt, timezone.get_current_timezone())

        diff_seconds = (entrada_dt - prog_aware).total_seconds()

        return int(diff_seconds // 60)

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

class Pase(models.Model):
    TIPO_CHOICES = [
        ('entrada', 'Pase de Entrada'),
        ('salida', 'Pase de Salida'),
    ]

    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name='pases')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    folio = models.CharField(max_length=50, unique=True)
    fecha = models.DateField(default=timezone.now)
    hora = models.TimeField()
    hora_reincorporacion = models.TimeField(blank=True, null=True, help_text='Hora de reincorporación (opcional)')
    asunto = models.CharField(max_length=255)
    observaciones = models.TextField(blank=True, null=True)
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='pases_creados')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    pdf_generado = models.FileField(upload_to='pases/', blank=True, null=True)

    class Meta:
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"Pase {self.folio} - {self.empleado} ({self.get_tipo_display()})"


class SystemConfig(models.Model):
    """Configuración sencilla editable desde admin.

    Usamos una tabla pequeña con una fila (primera fila usada) para valores globales.
    """
    retardo_minutos = models.PositiveIntegerField(default=5, help_text='Minutos de tolerancia para considerar un retardo')

    def __str__(self):
        return f"Configuración del sistema (retardo_minutos={self.retardo_minutos})"

    @classmethod
    def get_solo(cls):
        obj = cls.objects.first()
        if obj is None:
            obj = cls.objects.create()
        return obj
