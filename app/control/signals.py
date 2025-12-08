"""Signals para la app `control`.

Este módulo crea los grupos por defecto después de que se hayan
ejecutado las migraciones del app `auth`. Usamos `post_migrate`
y comprobamos `app_config.label == 'auth'` para ejecutarlo solo una
vez (cuando la app de autenticación haya sido migrada), evitando
problemas de orden.
"""
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.apps import apps
from django.db.models.signals import post_save
from django.dispatch import receiver as receiver2
from django.db.models.signals import post_delete
from django.conf import settings


@receiver(post_migrate)
def create_default_groups(sender, app_config, **kwargs):
	"""Crear los grupos por defecto cuando la app `auth` termine de migrar.

	Se ejecuta al finalizar las migraciones de cada app; aquí filtramos
	para que la creación se realice solo cuando la app migrada sea `auth`.
	"""
	# `app_config` es la AppConfig de la app que se acaba de migrar
	label = getattr(app_config, 'label', None)
	if label != 'auth':
		return

	Group = apps.get_model('auth', 'Group')

	grupos = ['administracion', 'empleado']
	for nombre in grupos:
		Group.objects.get_or_create(name=nombre)


# Signal: cuando un Justificante es aprobado, marcar la Asistencia como 'justificada'
@receiver2(post_save)
def justificar_asistencia_on_approval(sender, instance, created, **kwargs):
	"""Si un Justificante cambia a estado 'aprobado', actualizar la asistencia asociada.

	Usamos apps.get_model para evitar importaciones directas que puedan causar ciclos
	durante la carga de apps.
	"""
	# Evitar actuar sobre señales de otros modelos
	if sender.__name__ != 'Justificante':
		return

	# Si el justificante está aprobado, actualizar la asistencia a 'justificada'
	if instance.estado == 'aprobado' and instance.asistencia:
		asistencia = instance.asistencia
		# Solo actualizar si no está ya justificada
		if asistencia.tipo != 'justificada':
			asistencia.tipo = 'justificada'
			asistencia.save()

	# Si el justificante fue cambiado a 'rechazado', debemos revertir el tipo
	# solo si NO existen otros justificantes aprobados para la misma asistencia.
	# En ese caso recalculamos según la diferencia de minutos y el umbral.
	if instance.estado == 'rechazado' and instance.asistencia:
		asistencia = instance.asistencia
		# comprobar si quedan justificantes aprobados distintos al actual
		try:
			otros_aprobados = asistencia.justificantes.filter(estado='aprobado').exclude(pk=instance.pk).exists()
		except Exception:
			otros_aprobados = False

		if not otros_aprobados:
			# obtener el modelo SystemConfig de manera segura
			try:
				SystemConfig = apps.get_model('control', 'SystemConfig')
				cfg = SystemConfig.get_solo()
				umbral = int(cfg.retardo_minutos or 0)
			except Exception:
				umbral = 0

			# intentar recalcular minutos de diferencia; si no hay hora de entrada, poner 'normal'
			mins = None
			try:
				if hasattr(asistencia, 'compute_diferencia_minutes'):
					mins = asistencia.compute_diferencia_minutes()
			except Exception:
				mins = None

			nuevo_tipo = None
			if mins is None:
				nuevo_tipo = 'normal'
			else:
				try:
					if mins > umbral:
						nuevo_tipo = 'retardo'
					else:
						nuevo_tipo = 'normal'
				except Exception:
					nuevo_tipo = 'normal'

			if nuevo_tipo and asistencia.tipo != nuevo_tipo:
				asistencia.tipo = nuevo_tipo
				asistencia.save()


# Cuando se elimina un justificante, recomputar el estado de la asistencia asociada
@receiver2(post_delete)
def recompute_asistencia_on_justificante_delete(sender, instance, **kwargs):
	# Evitar actuar sobre señales de otros modelos
	if sender.__name__ != 'Justificante':
		return

	if not instance.asistencia:
		return

	asistencia = instance.asistencia
	# Si quedan justificantes aprobados, mantener 'justificada'
	try:
		quedan_aprobados = asistencia.justificantes.filter(estado='aprobado').exists()
	except Exception:
		quedan_aprobados = False

	if quedan_aprobados:
		return

	# No quedan justificantes aprobados: recalcular tipo como en el caso de rechazo
	try:
		SystemConfig = apps.get_model('control', 'SystemConfig')
		cfg = SystemConfig.get_solo()
		umbral = int(cfg.retardo_minutos or 0)
	except Exception:
		umbral = 0

	mins = None
	try:
		if hasattr(asistencia, 'compute_diferencia_minutes'):
			mins = asistencia.compute_diferencia_minutes()
	except Exception:
		mins = None

	if mins is None:
		nuevo_tipo = 'normal'
	else:
		try:
			nuevo_tipo = 'retardo' if mins > umbral else 'normal'
		except Exception:
			nuevo_tipo = 'normal'

	if asistencia.tipo != nuevo_tipo:
		asistencia.tipo = nuevo_tipo
		asistencia.save()

