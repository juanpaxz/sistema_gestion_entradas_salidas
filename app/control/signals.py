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

