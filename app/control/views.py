from django.shortcuts import render
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from .models import Empleado


# Create your views here.
def home(request):
	"""Vista principal de la app `control` para verificar que la app responde."""
	return HttpResponse("Control app: funciona correctamente.")


@login_required
def dashboard(request):
	"""Dashboard para administradores.

	Muestra métricas básicas del sistema (número de empleados, activos) y
	solo está disponible para usuarios del grupo 'administracion'.
	"""
	user = request.user
	# comprobar pertenencia al grupo administracion
	if not user.groups.filter(name='administracion').exists():
		return HttpResponseForbidden('No tienes permiso para ver esta página')

	total_empleados = Empleado.objects.count()
	activos = Empleado.objects.filter(estado='activo').count()

	context = {
		'total_empleados': total_empleados,
		'empleados_activos': activos,
	}
	return render(request, 'control/dashboard.html', context)
