from django.shortcuts import render
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import Group
from django.utils import timezone
from django.contrib.auth.views import LoginView
from django.db import IntegrityError
from datetime import datetime, date
import logging
from .models import Empleado, Asistencia, Horario
from .forms import EmpleadoCreationForm, EmpleadoForm, JustificanteRetardoForm, HorarioForm
# Configurar logger para la aplicación
logger = logging.getLogger(__name__)

class CustomLoginView(LoginView):
    template_name = 'control/login.html'
    
    def get_success_url(self):
        user = self.request.user
        
        if user.groups.filter(name='administracion').exists():
            return '/control/admin/dashboard/'
        elif user.groups.filter(name='empleado').exists():
            return '/control/empleado/dashboard/'
        elif user.groups.filter(name='supervisores').exists():
            return '/supervisores/panel/'
        else:
            return '/default/'  # Página por defecto

def es_administracion(user):
    return user.groups.filter(name='administracion').exists()

# Create your views here.
def home(request):
    """Vista principal de la app `control` para verificar que la app responde."""
    return HttpResponse("Control app: funciona correctamente.")

@login_required
def listar_empleados(request):
    """Lista los empleados. Acceso solo para administradores."""
    user = request.user
    if not es_administracion(user):
        return HttpResponseForbidden('No tienes permiso para ver esta página')

    empleados = Empleado.objects.select_related('user').all().order_by('nombre', 'apellido')
    return render(request, 'control/administracion/listar_empleados.html', {'empleados': empleados})


@login_required
def dashboard(request):
    """Dashboard para administradores.

    Muestra métricas básicas del sistema (número de empleados, activos) y
    solo está disponible para usuarios del grupo 'administracion'.
    """
    user = request.user
    # comprobar pertenencia al grupo administracion
    if not es_administracion(user):
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
    if not es_administracion(user):
        return HttpResponseForbidden('No tienes permiso para ver esta página')

    if request.method == 'POST':
        form = EmpleadoCreationForm(request.POST)
        if form.is_valid():
            # Guardar usuario y empleado
            new_user = form.save(commit=True)
            logger.info(f"Usuario creado exitosamente: {new_user.username}")
            
            # Crear registro Empleado y manejar errores de integridad (RFC único)
            try:
                empleado = Empleado.objects.create(
                    user=new_user,
                    nombre=form.cleaned_data.get('nombre'),
                    apellido=form.cleaned_data.get('apellido'),
                    puesto=form.cleaned_data.get('puesto'),
                    estado=form.cleaned_data.get('estado'),
                    rfc=form.cleaned_data.get('rfc'),
                    huella_biometrica=form.cleaned_data.get('huella_biometrica') or None,
                )
                # Asignar horarios opcionales seleccionados en el formulario
                horarios_selected = form.cleaned_data.get('horarios')
                if horarios_selected:
                    empleado.horarios.set(horarios_selected)
                logger.info(f"Empleado creado exitosamente: {empleado.nombre} {empleado.apellido} (RFC: {empleado.rfc})")
                
                # Asignar al grupo seleccionado en el formulario (role). Fallback a 'empleado'
                selected_role = form.cleaned_data.get('role', 'empleado')
                try:
                    grupo = Group.objects.get(name=selected_role)
                    new_user.groups.add(grupo)
                    logger.info(f"Usuario {new_user.username} añadido al grupo '{selected_role}'")
                except Group.DoesNotExist:
                    logger.warning(f"El grupo '{selected_role}' no existe en el sistema")
                
                # Si todo fue exitoso, mostrar mensaje y redirigir
                messages.success(request, f'Empleado {empleado.nombre} {empleado.apellido} creado correctamente')
                return redirect('control:admin_dashboard')
                    
            except IntegrityError as e:
                logger.error(f"Error de integridad al crear empleado con RFC {form.cleaned_data.get('rfc')}: {str(e)}")
                new_user.delete()
                form.add_error('rfc', 'Ya existe un empleado con ese RFC o ocurrió un conflicto en la base de datos.')
                
            except Exception as e:
                logger.error(f"Error inesperado al crear empleado: {str(e)}", exc_info=True)
                new_user.delete()
                messages.error(request, f'Ocurrió un error al crear el empleado: {str(e)}')

                messages.success(request, 'Empleado creado correctamente.')
                return redirect('control:admin_dashboard')
    else:
        form = EmpleadoCreationForm()

    return render(request, 'control/administracion/crear_empleado.html', {'form': form})


@login_required
def editar_empleado(request, empleado_id):
    """Editar los datos de un empleado existente."""
    user = request.user
    if not es_administracion(user):
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
    if not es_administracion(user):
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


@login_required
def listar_horarios(request):
    """Lista los horarios -- acceso solo administradores."""
    user = request.user
    if not es_administracion(user):
        return HttpResponseForbidden('No tienes permiso para ver esta página')

    horarios = Horario.objects.all().order_by('nombre')
    return render(request, 'control/administracion/horarios_list.html', {'horarios': horarios})


@login_required
def crear_horario(request):
    user = request.user
    if not es_administracion(user):
        return HttpResponseForbidden('No tienes permiso para ver esta página')

    if request.method == 'POST':
        form = HorarioForm(request.POST)
        if form.is_valid():
            horario = form.save()
            messages.success(request, 'Horario creado correctamente.')
            return redirect('control:listar_horarios')
    else:
        form = HorarioForm()

    return render(request, 'control/administracion/crear_horario.html', {'form': form})


@login_required
def editar_horario(request, horario_id):
    user = request.user
    if not es_administracion(user):
        return HttpResponseForbidden('No tienes permiso para ver esta página')

    horario = get_object_or_404(Horario, pk=horario_id)
    if request.method == 'POST':
        form = HorarioForm(request.POST, instance=horario)
        if form.is_valid():
            form.save()
            messages.success(request, 'Horario actualizado correctamente.')
            return redirect('control:listar_horarios')
    else:
        form = HorarioForm(instance=horario)

    return render(request, 'control/administracion/crear_horario.html', {'form': form, 'horario': horario})


@login_required
def eliminar_horario(request, horario_id):
    user = request.user
    if not es_administracion(user):
        return HttpResponseForbidden('No tienes permiso para ver esta página')

    horario = get_object_or_404(Horario, pk=horario_id)
    if request.method == 'POST':
        horario.delete()
        messages.success(request, 'Horario eliminado correctamente.')
        return redirect('control:listar_horarios')

    return render(request, 'control/administracion/confirm_delete_horario.html', {'horario': horario})


def registro_asistencia(request):
    """Vista completamente pública para el registro de asistencias."""

    
    return render(request, 'control/asistencias/registro.html')


def registrar_entrada(request):
    """Registrar la entrada de un empleado."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

    # Priorizar RFC enviado en el POST (permitir kioscos/public access)
    rfc = request.POST.get('rfc')
    empleado = None

    if rfc:
        try:
            empleado = Empleado.objects.get(rfc__iexact=rfc)
        except Empleado.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'No se encontró empleado con ese RFC'}, status=404)

    # Verificar si ya existe una asistencia para hoy
    asistencia, created = Asistencia.objects.get_or_create(
        empleado=empleado,
        fecha=date.today()
    )
    if asistencia.hora_entrada:
        return JsonResponse({
            'status': 'error',
            'message': 'Ya has registrado tu entrada hoy'
        })

    # Registrar la hora de entrada
    asistencia.registrar_entrada()

    # Verificar si es un retardo (puedes ajustar la hora límite según tus necesidades)
    hora_actual = timezone.localtime(asistencia.hora_entrada).time()
    hora_limite = datetime.strptime('09:00', '%H:%M').time()

    if hora_actual > hora_limite:
        asistencia.tipo = 'retardo'
        asistencia.save()

    return JsonResponse({
        'status': 'success',
        'message': 'Entrada registrada exitosamente',
        # Mostrar la hora en la zona local del servidor
        'hora': timezone.localtime(asistencia.hora_entrada).strftime('%H:%M:%S')
    })


def registrar_salida(request):
    """Registrar la salida de un empleado."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

    # Priorizar RFC enviado en el POST
    rfc = request.POST.get('rfc')
    empleado = None

    if rfc:
        try:
            empleado = Empleado.objects.get(rfc__iexact=rfc)
        except Empleado.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'No se encontró empleado con ese RFC'}, status=404)

    # Buscar la asistencia de hoy
    try:
        asistencia = Asistencia.objects.get(
            empleado=empleado,
            fecha=date.today()
        )

        if not asistencia.hora_entrada:
            return JsonResponse({
                'status': 'error',
                'message': 'Debes registrar primero tu entrada'
            })

        if asistencia.hora_salida:
            return JsonResponse({
                'status': 'error',
                'message': 'Ya has registrado tu salida hoy'
            })

        # Registrar la hora de salida
        asistencia.registrar_salida()

        return JsonResponse({
            'status': 'success',
            'message': 'Salida registrada exitosamente',
            # Mostrar la hora en la zona local del servidor
            'hora': timezone.localtime(asistencia.hora_salida).strftime('%H:%M:%S')
        })

    except Asistencia.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'No se encontró registro de entrada para hoy'
        })


@login_required
def ver_asistencias(request):
    """Ver el historial de asistencias."""
    user = request.user

    # Si es administrador, puede ver todas las asistencias
    if es_administracion(user):
        asistencias = Asistencia.objects.all().select_related('empleado')
    else:
        # Si es empleado, solo ve sus propias asistencias
        try:
            empleado = Empleado.objects.get(user=user)
            asistencias = Asistencia.objects.filter(empleado=empleado)
        except Empleado.DoesNotExist:
            return HttpResponseForbidden('No tienes acceso a esta página')

    # Ordenar por fecha descendente
    asistencias = asistencias.order_by('-fecha', '-hora_entrada')

    return render(request, 'control/asistencias/empleado_dashboard.html', {
        'asistencias': asistencias
    })


@login_required
def reporte_asistencias(request):
    """Generar reporte de asistencias (solo administradores)."""
    if not request.user.groups.filter(name='administracion').exists():
        return HttpResponseForbidden('No tienes permiso para ver esta página')

    # Obtener parámetros de filtrado
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    empleado_id = request.GET.get('empleado_id')
    tipo = request.GET.get('tipo')

    # Construir el query base
    asistencias = Asistencia.objects.all().select_related('empleado')

    # Aplicar filtros si existen
    if fecha_inicio:
        asistencias = asistencias.filter(fecha__gte=fecha_inicio)
    if fecha_fin:
        asistencias = asistencias.filter(fecha__lte=fecha_fin)
    if empleado_id:
        asistencias = asistencias.filter(empleado_id=empleado_id)
    if tipo:
        asistencias = asistencias.filter(tipo=tipo)

    # Obtener lista de empleados para el filtro
    empleados = Empleado.objects.filter(estado='activo').order_by('nombre')

    return render(request, 'control/asistencias/reporte.html', {
        'asistencias': asistencias,
        'empleados': empleados,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'empleado_id': empleado_id,
        'tipo': tipo
    })


@login_required
def subir_justificante(request, asistencia_id):
    """Subir justificante PDF para un retardo."""
    asistencia = get_object_or_404(Asistencia, pk=asistencia_id)
    user = request.user
    
    # Validar que el empleado solo pueda subir justificantes para sus propias asistencias
    try:
        empleado = Empleado.objects.get(user=user)
        if asistencia.empleado != empleado:
            return HttpResponseForbidden('No tienes permiso para modificar este registro')
    except Empleado.DoesNotExist:
        return HttpResponseForbidden('No tienes acceso a esta página')
    
    # Validar que solo se puedan subir justificantes para retardos
    if asistencia.tipo != 'retardo':
        messages.error(request, 'Solo puedes subir justificantes para asistencias con retardo.')
        return redirect('control:empleado_dashboard')
    
    if request.method == 'POST':
        form = JustificanteRetardoForm(request.POST, request.FILES, instance=asistencia)
        if form.is_valid():
            form.save()
            messages.success(request, 'Justificante subido exitosamente.')
            return redirect('control:empleado_dashboard')
        else:
            messages.error(request, 'Error al subir el justificante. Verifique el archivo.')
    else:
        form = JustificanteRetardoForm(instance=asistencia)
    
    return render(request, 'control/asistencias/subir_justificante.html', {
        'form': form,
        'asistencia': asistencia
    })
