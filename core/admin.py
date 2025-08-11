from django.contrib import admin
from .models import Activo, FortiSwitch

class FortiSwitchInline(admin.TabularInline):
    model = FortiSwitch
    extra = 1
    fields = ('modelo_equipo', 'serie', 'oblea')
    show_change_link = True

@admin.register(Activo)
class ActivoAdmin(admin.ModelAdmin):
    list_display = (
        'comando_region', 'titulo_abreviado', 'modelo_equipo_fortinet',
        'serie_fortinet', 'ip_admin', 'estado', 'apellido_nombre_admin',
        'fecha_creacion'
    )
    search_fields = (
        'comando_region', 'titulo_abreviado', 'modelo_equipo_fortinet',
        'serie_fortinet', 'ip_admin', 'apellido_nombre_admin', 'oblea_fortinet'
    )
    list_filter = ('comando_region', 'modelo_equipo_fortinet', 'estado')
    ordering = ('comando_region', 'ip_admin')
    date_hierarchy = 'fecha_creacion'
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')
    inlines = [FortiSwitchInline]

    fieldsets = (
        ('Datos del Equipo (Fortinet)', {
            'fields': ('comando_region', 'titulo_abreviado', 'detalle_unidad',
                       'modelo_equipo_fortinet', 'serie_fortinet', 'oblea_fortinet')
        }),
        ('Datos de Red', {
            'fields': ('ospf', 'ip_admin', 'direccion_subred', 'red_dmz', 'red_wifi')
        }),
        ('Estado', {'fields': ('estado',)}),
        ('Datos Administrador de Unidad', {
            'fields': ('grupo_admin_ldap', 'apellido_nombre_admin', 'telefono_admin')
        }),
        ('Observaciones', {'fields': ('observaciones',)}),
        ('Metadatos', {'fields': ('fecha_creacion', 'fecha_actualizacion')}),
    )
