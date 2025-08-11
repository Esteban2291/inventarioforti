# core/views_roles.py
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib.auth.models import User, Group
from django.core.paginator import Paginator
from django.db.models import Prefetch
from django.shortcuts import redirect, render

@login_required
@user_passes_test(lambda u: u.is_staff)
def gestionar_usuarios_view(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        role = request.POST.get('role')  # '', 'administrador' o 'operador'
        try:
            u = User.objects.get(pk=user_id)
            # No permitir quitarse a uno mismo el último rol admin (opcional reforzar)
            admin_group = Group.objects.get(name='administrador')
            op_group = Group.objects.get(name='operador')

            # Limpio ambos y asigno si corresponde
            u.groups.remove(admin_group, op_group)
            if role == 'administrador':
                u.groups.add(admin_group)
            elif role == 'operador':
                u.groups.add(op_group)

            messages.success(request, f"Rol actualizado para {u.username}.")
        except Exception as e:
            messages.error(request, f"Error: {e}")
        return redirect('gestionar_usuarios')

    qs = User.objects.all().select_related().prefetch_related('groups')
    paginator = Paginator(qs, 20)
    page = request.GET.get('page')
    users = paginator.get_page(page)

    rows = []
    for u in users:
        current_role = u.groups.first().name if u.groups.exists() else None
        rows.append({'user': u, 'current_role': current_role})

    return render(request, 'gestionar_usuarios.html', {
        'rows': rows,
        'users': users,  # para controles de paginación
    })


@login_required
@user_passes_test(lambda u: u.is_staff)  # solo staff puede entrar
def gestionar_roles_permisos_view(request):
    roles = Group.objects.prefetch_related('permissions').all()
    return render(request, 'gestionar_roles_permisos.html', {'roles': roles})