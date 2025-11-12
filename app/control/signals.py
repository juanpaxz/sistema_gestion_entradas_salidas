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

	# Si el justificante está aprobado, actualizar la asistencia
	if instance.estado == 'aprobado' and instance.asistencia:
		asistencia = instance.asistencia
		# Solo actualizar si no está ya justificada
		if asistencia.tipo != 'justificada':
			asistencia.tipo = 'justificada'
			asistencia.save()

