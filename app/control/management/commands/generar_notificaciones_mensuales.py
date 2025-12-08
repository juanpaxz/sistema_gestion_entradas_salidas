from django.core.management.base import BaseCommand
from django.utils import timezone
from ...models import Asistencia, Notificacion
import datetime

class Command(BaseCommand):
    help = 'Genera notificaciones internas recordando justificar faltas del mes anterior (sin enviar emails).'

    def handle(self, *args, **options):
        today = timezone.now().date()
        first_day_this_month = today.replace(day=1)
        last_month_last_day = first_day_this_month - datetime.timedelta(days=1)
        last_month_first_day = last_month_last_day.replace(day=1)

        self.stdout.write(f'Generando notificaciones para faltas entre {last_month_first_day} y {last_month_last_day}')

        faltas = Asistencia.objects.filter(tipo='falta', fecha__gte=last_month_first_day, fecha__lte=last_month_last_day).select_related('empleado')

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
            periodo_tag = last_month_first_day.strftime('%Y-%m')
            titulo = 'Recordatorio: faltas sin justificar'
            mensaje = f'[{periodo_tag}] Tienes faltas sin justificar en: ' + ', '.join(fechas) + '. Por favor sube los justificantes.'

            # Evitar crear duplicados para el mismo empleado/periodo/titulo
            existe = Notificacion.objects.filter(empleado=emp, periodo=periodo_tag, titulo=titulo).exists()
            if existe:
                self.stdout.write(f'Ya existe notificación para {emp} ({periodo_tag}), se omite')
                continue

            Notificacion.objects.create(empleado=emp, titulo=titulo, mensaje=mensaje, periodo=periodo_tag)
            created += 1
            self.stdout.write(f'Notificación creada para {emp}')

        self.stdout.write(f'Creadas {created} notificaciones.')
