from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from core.models import Activo  # reemplazá si tu modelo está en otra app

class Command(BaseCommand):
    help = 'Crea grupos y asigna permisos'

    def handle(self, *args, **options):
        # Crear grupo Admin
        admin_group, _ = Group.objects.get_or_create(name='Administrador')
        supervisor_group, _ = Group.objects.get_or_create(name='Supervisor')
        usuario_group, _ = Group.objects.get_or_create(name='Usuario')

        content_type = ContentType.objects.get_for_model(Activo)

        permisos_basicos = Permission.objects.filter(content_type=content_type)

        # Administrador: todos los permisos
        admin_group.permissions.set(permisos_basicos)

        # Supervisor: solo ver y cambiar
        permisos_supervisor = permisos_basicos.filter(codename__in=['view_activo', 'change_activo'])
        supervisor_group.permissions.set(permisos_supervisor)

        # Usuario: solo ver
        permisos_usuario = permisos_basicos.filter(codename='view_activo')
        usuario_group.permissions.set(permisos_usuario)

        self.stdout.write(self.style.SUCCESS("Grupos y permisos creados correctamente"))
