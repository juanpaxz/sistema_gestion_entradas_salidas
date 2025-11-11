
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'control'

# Ruta para la vista de inicio de sesión
urlpatterns = [
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    # Rutas para la gestión de empleados
    path('admin/dashboard/', views.dashboard, name='admin_dashboard'),
    path('crear/', views.crear_empleado, name='crear'),
    path('listar/', views.listar_empleados, name='listar'),
    path('<int:empleado_id>/editar/', views.editar_empleado, name='editar'),
    path('<int:empleado_id>/eliminar/', views.eliminar_empleado, name='eliminar'),
    path('asistencia/reporte/', views.reporte_asistencias, name='reporte_asistencias'),

    # Rutas para el control de asistencia
    path('', views.registro_asistencia, name='registro_asistencia'),
    path('entrada/', views.registrar_entrada, name='registrar_entrada'),
    path('salida/', views.registrar_salida, name='registrar_salida'),
    # Horarios CRUD para administradores
    path('horarios/', views.listar_horarios, name='listar_horarios'),
    path('horarios/crear/', views.crear_horario, name='crear_horario'),
    path('horarios/<int:horario_id>/editar/', views.editar_horario, name='editar_horario'),
    path('horarios/<int:horario_id>/eliminar/', views.eliminar_horario, name='eliminar_horario'),

    # Dashboard específico para empleados (mapea al historial de asistencias)
    path('empleado/dashboard/', views.ver_asistencias, name='empleado_dashboard'),
    path('asistencia/<int:asistencia_id>/subir-justificante/', views.subir_justificante, name='subir_justificante'),
]
