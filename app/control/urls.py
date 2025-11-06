
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'control'

# Ruta para la vista de inicio de sesión
urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='control/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    # Rutas para la gestión de empleados
    path('crear/', views.crear_empleado, name='crear'),
    path('listar/', views.listar_empleados, name='listar'),
    path('<int:empleado_id>/editar/', views.editar_empleado, name='editar'),
    path('<int:empleado_id>/eliminar/', views.eliminar_empleado, name='eliminar'),

    # Rutas para el control de asistencia
    path('asistencia/', views.registro_asistencia, name='registro_asistencia'),
    path('asistencia/entrada/', views.registrar_entrada, name='registrar_entrada'),
    path('asistencia/salida/', views.registrar_salida, name='registrar_salida'),
    path('asistencia/historial/', views.ver_asistencias, name='ver_asistencias'),
    path('asistencia/reporte/', views.reporte_asistencias, name='reporte_asistencias'),
]

