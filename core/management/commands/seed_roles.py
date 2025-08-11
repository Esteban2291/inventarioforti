from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission

class Command(BaseCommand):
    help = "Crea/actualiza roles base (administrador, operador)"

    def handle(self, *args, **kwargs):
        admin_group, _ = Group.objects.get_or_create(name="administrador")
        op_group, _ = Group.objects.get_or_create(name="operador")

        all_perms = Permission.objects.all()
        view_perms = Permission.objects.filter(codename__startswith="view_")

        admin_group.permissions.set(all_perms)   # acceso total
        op_group.permissions.set(view_perms)     # sólo lectura

        self.stdout.write(self.style.SUCCESS("Roles actualizados: administrador, operador"))
