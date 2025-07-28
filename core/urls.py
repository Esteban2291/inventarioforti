from django.urls import path
from . import views
from django.contrib.auth import views as auth_views # Importa las vistas de autenticación de Django

urlpatterns = [
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('activos/', views.lista_activos, name='listado_activos'),
    path('activos/crear/', views.crear_activo_view, name='crear_activo'),
    path('activos/editar/<int:pk>/', views.editar_activo_view, name='editar_activo'),
    path('eliminar/<int:pk>/', views.eliminar_activo_view, name='eliminar_activo'),
    path('importar/', views.importar_activos_view, name='importar_activos'),
    path('activos/<int:pk>/detalle/', views.detalle_activo_view, name='detalle_activo'),
    path('activos/<int:pk>/agregar-switch/', views.agregar_switch_a_activo, name='agregar_switch'),
]