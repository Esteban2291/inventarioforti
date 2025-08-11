from django.urls import path
from . import views
#from django.contrib.auth import views as auth_views
from .views import CustomLoginView, CustomLogoutView
from .views import gestionar_usuarios_view, gestionar_roles_permisos_view

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'), 
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # Activos
    path('activos/', views.listar_activos_view, name='listar_activos'),
    path('activos/crear/', views.crear_activo_view, name='crear_activo'),
    path('activos/editar/<int:pk>/', views.editar_activo_view, name='editar_activo'),
    path('activos/eliminar/<int:pk>/', views.eliminar_activo_view, name='eliminar_activo'),
    path('activos/<int:pk>/detalle/', views.detalle_activo_view, name='detalle_activo'),
    path('activos/<int:pk>/agregar-switch/', views.agregar_switch_a_activo, name='agregar_switch'),
    path('activos/importar/', views.importar_activos_view, name='importar_activos'),
    path('usuarios/', gestionar_usuarios_view, name='gestionar_usuarios'),
    path('usuarios/roles-permisos/', gestionar_roles_permisos_view, name='gestionar_roles_permisos'),
]
