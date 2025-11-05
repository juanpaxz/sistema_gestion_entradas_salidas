
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
    #path('crear/', views.crear_empleado, name='crear'),
    #path('<int:empleado_id>/', views.detalle_empleado, name='detalle'),
    #path('<int:empleado_id>/editar/', views.editar_empleado, name='editar'),
    #path('<int:empleado_id>/eliminar/', views.eliminar_empleado, name='eliminar'),

]

