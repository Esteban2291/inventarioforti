from django.contrib import admin
from .models import Activo

# Clase para personalizar cómo se muestra el modelo Activo en el admin
class ActivoAdmin(admin.ModelAdmin):
    list_display = (
        'comando_region', 'titulo_abreviado', 'modelo_equipo_fortinet',
        'serie_fortinet', 'ip_admin', 'apellido_nombre_admin',
        'fecha_creacion'
    )
    search_fields = (
        'comando_region', 'titulo_abreviado', 'serie_fortinet',
        'ip_admin', 'apellido_nombre_admin'
    )
    list_filter = ('comando_region', 'modelo_equipo_fortinet')
    ordering = ('comando_region', 'ip_admin')
    # Añadir campos para agrupar en el formulario de edición/creación
    fieldsets = (
        ('Datos del Equipo (Fortinet)', {
            'fields': ('comando_region', 'titulo_abreviado', 'detalle_unidad',
            'modelo_equipo_fortinet', 'serie_fortinet', 'oblea_fortinet')
        }),
        ('Datos de Red', {
            'fields': ('ospf', 'ip_admin', 'direccion_subred', 'red_dmz', 'red_wifi')
        }),
        ('Datos Administrador de Unidad', {
            'fields': ('grupo_admin_ldap', 'apellido_nombre_admin', 'telefono_admin')
        }),
        ('Observaciones', {
            'fields': ('observaciones',),
        }),
    )
admin.site.register(Activo, ActivoAdmin)