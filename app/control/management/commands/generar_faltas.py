from django.core.management.base import BaseCommand
from django.utils import timezone
from control.models import Empleado, Asistencia
import datetime


class Command(BaseCommand):
    help = "Genera faltas automáticamente para un día (por defecto hoy)."

    def add_arguments(self, parser):
        parser.add_argument('--fecha', type=str, help='Fecha en formato YYYY-MM-DD (opcional).')
        parser.add_argument('--dry-run', action='store_true', help='No persiste cambios; solo muestra qué se haría.')

    def handle(self, *args, **options):
        fecha_str = options.get('fecha')
        dry = options.get('dry_run')

        if fecha_str:
            try:
                fecha = datetime.datetime.strptime(fecha_str, '%Y-%m-%d').date()
            except Exception:
                self.stderr.write(self.style.ERROR('Formato de fecha inválido. Use YYYY-MM-DD'))
                return
        else:
            fecha = timezone.localdate()

        created = 0
        now = timezone.localtime()
        for emp in Empleado.objects.all():
            # 1) comprobar si el empleado tiene horario para la fecha
            try:
                horario = emp.get_horario_para_fecha(fecha)
            except Exception:
                horario = None

            if not horario:
                continue

            # Construir datetime programado de salida
            try:
                scheduled_dt = datetime.datetime.combine(fecha, horario.hora_salida)
                try:
                    scheduled_dt = timezone.make_aware(scheduled_dt, timezone.get_current_timezone())
                except Exception:
                    pass
            except Exception:
                scheduled_dt = None

            # Determinar si ya pasó la hora de salida para la fecha indicada
            passed = False
            if fecha < now.date():
                passed = True
            elif fecha == now.date():
                if scheduled_dt is None:
                    passed = True
                else:
                    passed = now >= scheduled_dt
            else:
                passed = False

            # 2) comprobar si ya existe asistencia
            asistencia_qs = Asistencia.objects.filter(empleado=emp, fecha=fecha)
            if asistencia_qs.exists():
                asistencia = asistencia_qs.first()
                # Si existe pero no tiene hora_salida y ya pasó la hora programada, marcar falta
                if asistencia.hora_salida is None and passed:
                    if dry:
                        self.stdout.write(f"[DRY] Marcaría falta en asistencia existente para: {emp} ({emp.rfc}) - {fecha}")
                    else:
                        # No sobrescribir justificadas
                        if asistencia.tipo != 'justificada':
                            asistencia.tipo = 'falta'
                            obs = asistencia.observaciones or ''
                            asistencia.observaciones = (obs + ' | Falta generada automáticamente').strip(' |')
                            asistencia.save()
                            created += 1
                continue

            # 3) Si no hay asistencia: sólo crear falta si ya pasó la hora de salida (o fecha anterior)
            if not passed:
                continue

            if dry:
                self.stdout.write(f"[DRY] Generaría falta para: {emp} ({emp.rfc}) - {fecha}")
            else:
                Asistencia.objects.create(
                    empleado=emp,
                    fecha=fecha,
                    tipo='falta',
                    observaciones='Falta generada automáticamente'
                )
                created += 1

        if dry:
            self.stdout.write(self.style.SUCCESS('Dry-run completado.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Faltas generadas correctamente: {created}'))
