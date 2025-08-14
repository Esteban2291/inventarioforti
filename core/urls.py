from django.urls import path
from . import views
from .views import CustomLoginView, CustomLogoutView
from .views import gestionar_usuarios_view, gestionar_roles_permisos_view

urlpatterns = [
    # Auth
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),

    # Dashboard
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # Activos
    path('activos/', views.listar_activos_view, name='listar_activos'),
    path('activos/crear/', views.crear_activo_view, name='crear_activo'),
    path('activos/editar/<int:pk>/', views.editar_activo_view, name='editar_activo'),
    path('activos/eliminar/<int:pk>/', views.eliminar_activo_view, name='eliminar_activo'),
    path('activos/<int:pk>/detalle/', views.detalle_activo_view, name='detalle_activo'),

    # FortiSwitch asociado
    path('activos/<int:pk>/agregar-switch/', views.agregar_switch_a_activo, name='agregar_switch'),

    # Importar (stub con template)
    path('activos/importar/', views.importar_activos_view, name='importar_activos'),

    # Gestión de usuarios / roles
    path("gestionar-usuarios/", views.gestionar_usuarios_view, name="gestionar_usuarios"),
    path("gestionar-roles-permisos/", views.gestionar_roles_permisos_view, name="gestionar_roles_permisos"),

    #Importar Excel
    path('importar_excel/', views.importar_excel_view, name='importar_excel'),


    # core/urls.py
    path('activos/exportar/excel/', views.exportar_activos_excel, name='exportar_activos_excel'),
    path('activos/exportar/pdf/', views.exportar_activos_pdf, name='exportar_activos_pdf'),

]

     