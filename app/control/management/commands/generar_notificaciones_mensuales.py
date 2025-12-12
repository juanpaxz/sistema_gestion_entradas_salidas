from django.core.management.base import BaseCommand
from django.utils import timezone
from ...models import Asistencia, Notificacion
import datetime
import calendar

class Command(BaseCommand):
    help = 'Genera notificaciones internas recordando justificar faltas y retardos de todo el mes actual (sin enviar emails).'

    def handle(self, *args, **options):
        today = timezone.now().date()
        year, month = today.year, today.month
        first_day_date = today.replace(day=1)
        last_day = calendar.monthrange(year, month)[1]
        last_day_date = today.replace(day=last_day)

        self.stdout.write(f'Generando notificaciones para faltas/retardos entre {first_day_date} y {last_day_date} (mes actual)')

        faltas = Asistencia.objects.filter(
            tipo__in=['falta', 'retardo'],
            fecha__gte=first_day_date,
            fecha__lte=last_day_date
        ).select_related('empleado')

        empleados = {}
        for f in faltas:
            # comprobar si tiene justificante aprobado
            aprob = f.justificantes.filter(estado='aprobado').exists()
            if aprob:
                continue
            emp = f.empleado
            empleados.setdefault(emp.pk, {'empleado': emp, 'fechas': []})
            empleados[emp.pk]['fechas'].append(f.fecha.strftime('%d/%m/%Y'))

        created = 0
        for data in empleados.values():
            emp = data['empleado']
            fechas = data['fechas']
            # periodo en formato YYYY-MM para identificar el mes objetivo
            periodo_tag = last_day_date.strftime('%Y-%m')
            titulo = 'Recordatorio: asistencias sin justificar (mes)'
            mensaje = (
                f'[{periodo_tag}] Tienes faltas/retardos sin justificar en el mes: '
                + ', '.join(fechas) + '. Por favor sube los justificantes.'
            )

            # Evitar crear duplicados para el mismo empleado/periodo/titulo
            existe = Notificacion.objects.filter(empleado=emp, periodo=periodo_tag, titulo=titulo).exists()
            if existe:
                self.stdout.write(f'Ya existe notificación para {emp} ({periodo_tag}), se omite')
                continue

            Notificacion.objects.create(empleado=emp, titulo=titulo, mensaje=mensaje, periodo=periodo_tag)
            created += 1
            self.stdout.write(f'Notificación creada para {emp}')

        self.stdout.write(f'Creadas {created} notificaciones.')
