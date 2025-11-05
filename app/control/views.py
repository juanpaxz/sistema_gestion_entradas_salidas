from django.shortcuts import render
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import Group

from .models import Empleado
from .forms import EmpleadoCreationForm
from .forms import EmpleadoForm
from django.shortcuts import get_object_or_404


@login_required
def listar_empleados(request):
	"""Lista los empleados. Acceso solo para administradores."""
	user = request.user
	if not user.groups.filter(name='administracion').exists():
		return HttpResponseForbidden('No tienes permiso para ver esta página')

	empleados = Empleado.objects.select_related('user').all().order_by('nombre', 'apellido')
	return render(request, 'control/administracion/listar_empleados.html', {'empleados': empleados})


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
	return render(request, 'control/administracion/dashboard.html', context)


@login_required
def crear_empleado(request):
	"""Crear un nuevo empleado (crea también el usuario asociado).

	Solo usuarios del grupo 'administracion' pueden acceder a esta vista.
	"""
	user = request.user
	if not user.groups.filter(name='administracion').exists():
		return HttpResponseForbidden('No tienes permiso para ver esta página')

	if request.method == 'POST':
		form = EmpleadoCreationForm(request.POST)
		if form.is_valid():
			# save user
			new_user = form.save(commit=True)
			# create Empleado record
			Empleado.objects.create(
				user=new_user,
				nombre=form.cleaned_data.get('nombre'),
				apellido=form.cleaned_data.get('apellido'),
				puesto=form.cleaned_data.get('puesto'),
				estado=form.cleaned_data.get('estado'),
				rfc=form.cleaned_data.get('rfc'),
				huella_biometrica=form.cleaned_data.get('huella_biometrica') or None,
			)
			# assign to 'empleado' group if it exists
			try:
				grupo = Group.objects.get(name='empleado')
				new_user.groups.add(grupo)
			except Group.DoesNotExist:
				pass

			messages.success(request, 'Empleado creado correctamente.')
			return redirect('control:dashboard')
	else:
		form = EmpleadoCreationForm()

	return render(request, 'control/administracion/crear_empleado.html', {'form': form})


@login_required
def editar_empleado(request, empleado_id):
	"""Editar los datos de un empleado existente."""
	user = request.user
	if not user.groups.filter(name='administracion').exists():
		return HttpResponseForbidden('No tienes permiso para ver esta página')

	empleado = get_object_or_404(Empleado, pk=empleado_id)
	if request.method == 'POST':
		form = EmpleadoForm(request.POST, instance=empleado)
		if form.is_valid():
			form.save()
			messages.success(request, 'Empleado actualizado correctamente.')
			return redirect('control:listar')
	else:
		form = EmpleadoForm(instance=empleado)

	return render(request, 'control/administracion/editar_empleado.html', {'form': form, 'empleado': empleado})


@login_required
def eliminar_empleado(request, empleado_id):
	"""Eliminar un empleado (confirma antes de borrar)."""
	user = request.user
	if not user.groups.filter(name='administracion').exists():
		return HttpResponseForbidden('No tienes permiso para ver esta página')

	empleado = get_object_or_404(Empleado, pk=empleado_id)
	if request.method == 'POST':
		# delete associated user (this cascades to empleado normally)
		try:
			empleado.user.delete()
		except Exception:
			empleado.delete()
		messages.success(request, 'Empleado eliminado correctamente.')
		return redirect('control:listar')

	return render(request, 'control/administracion/confirm_delete_empleado.html', {'empleado': empleado})
