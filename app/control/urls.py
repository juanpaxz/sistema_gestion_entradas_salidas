
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
    path('asistencia/reporte/exportar/', views.exportar_asistencias_excel, name='exportar_asistencias_excel'),

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
    path('empleado/events/', views.asistencia_events, name='asistencia_events'),
    path('empleado/dashboard/', views.ver_asistencias, name='empleado_dashboard'),
    path('asistencia/<int:asistencia_id>/subir-justificante/', views.subir_justificante, name='subir_justificante'),
    
    # Validación de justificantes (solo admin)
    path('admin/justificantes/', views.validar_justificantes, name='validar_justificantes'),
    path('admin/justificantes/<int:justificante_id>/aprobar/', views.aprobar_justificante, name='aprobar_justificante'),
    path('admin/justificantes/<int:justificante_id>/rechazar/', views.rechazar_justificante, name='rechazar_justificante'),
]
