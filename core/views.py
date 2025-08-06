from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib import messages
from django.utils import timezone
from .forms import LdapLoginForm
from helpers.ldap_helper import LdapHelper  # ✅ esto sí funciona
from django.contrib.auth import login
from django.contrib.auth.models import User
from .models import Activo, EstadoHistorico
from django.urls import reverse_lazy



from .forms import (
    ActivoForm,
    ImportarExcelForm,
    FortiSwitchForm,
    FortiSwitchFormSet,
    CambiarEstadoForm
)
# ---------------------------
# Autenticación personalizada
# ---------------------------
# ---------------------------
# Autenticación personalizada con LDAP
# ---------------------------
class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    redirect_authenticated_user = True
    authentication_form = LdapLoginForm

    def form_valid(self, form):
        dni = form.cleaned_data.get('dni')
        password = form.cleaned_data.get('password')

        if LdapHelper.autenticar_ldap(dni, password):
            user, created = User.objects.get_or_create(username=dni)
            login(self.request, user)
            messages.success(self.request, '¡Bienvenido!')
            return redirect('dashboard')
        else:
            form.add_error(None, "Credenciales inválidas.")
            return self.form_invalid(form)

class CustomLogoutView(LogoutView):
    next_page = 'login'

    def dispatch(self, request, *args, **kwargs):
        messages.info(self.request, 'Sesión cerrada.')
        return super().dispatch(request, *args, **kwargs)


# ---------------------------
# Vistas principales
# ---------------------------

def dashboard_view(request):
    total_activos = Activo.objects.count()
    activos_activos = Activo.objects.filter(estado='activo').count()
    activos_observacion = Activo.objects.filter(estado='observacion').count()
    activos_quemados = Activo.objects.filter(estado='quemado').count()
    activos_baja = Activo.objects.filter(estado='baja').count()

    context = {
        'total_activos': total_activos,
        'activos_activos': activos_activos,
        'activos_observacion': activos_observacion,
        'activos_quemados': activos_quemados,
        'activos_baja': activos_baja,
    }
    return render(request, 'dashboard.html', context)


@login_required
def listar_activos_view(request):
    activos = Activo.objects.all().prefetch_related('switches')
    return render(request, 'eliminar_activo.html', {
        'activos': activos,
        'titulo_pagina': 'Listado de Activos',
    })


@login_required
def crear_activo_view(request):
    if request.method == 'POST':
        form = ActivoForm(request.POST)
        formset = FortiSwitchFormSet(request.POST, prefix='switch')
        if form.is_valid() and formset.is_valid():
            activo = form.save()
            for sw in formset.save(commit=False):
                sw.activo = activo
                sw.save()
            EstadoHistorico.objects.create(
                activo=activo,
                estado_anterior=None,
                estado_nuevo=activo.estado,
                fecha_cambio=timezone.now()
            )
            messages.success(request, 'Activo y switches creados correctamente.')
            return redirect('listar_activos')
        messages.error(request, 'Error en el formulario.')
    else:
        form = ActivoForm()
        formset = FortiSwitchFormSet(prefix='switch')
    return render(request, 'activo_form.html', {
        'form': form,
        'formset': formset,
        'page_title': 'Crear Nuevo Activo'
    })

from .forms import CambiarEstadoForm  # ya lo usás

@login_required
def editar_activo_view(request, pk):
    activo = get_object_or_404(Activo, pk=pk)
    estado_original = activo.estado
    historial = EstadoHistorico.objects.filter(activo=activo).order_by('-fecha_cambio')

    if request.method == 'POST':
        form = ActivoForm(request.POST, instance=activo)
        formset = FortiSwitchFormSet(request.POST, instance=activo, prefix='switch')
        estado_form = CambiarEstadoForm(request.POST, instance=activo)

        if form.is_valid() and formset.is_valid() and estado_form.is_valid():
            # Primero actualizamos el estado si cambió
            nuevo_estado = estado_form.cleaned_data['estado']
            if nuevo_estado != estado_original:
                activo.estado = nuevo_estado
                activo.save()
                EstadoHistorico.objects.create(
                    activo=activo,
                    estado_anterior=estado_original,
                    estado_nuevo=nuevo_estado,
                    fecha_cambio=timezone.now()
                )

            # Luego guardamos el resto
            form.save()
            formset.save()

            messages.success(request, "Activo actualizado correctamente.")
            return redirect('listar_activos')
        else:
            # Mensaje y print para depurar
            messages.error(request, "Ocurrió un error al actualizar el activo.")
            print("Errores ActivoForm:", form.errors)
            print("Errores FormSet:", formset.errors)
            print("Errores EstadoForm:", estado_form.errors)

    else:
        form = ActivoForm(instance=activo)
        formset = FortiSwitchFormSet(instance=activo, prefix='switch')
        estado_form = CambiarEstadoForm(instance=activo)

    return render(request, 'editar_activo.html', {
        'form': form,
        'formset': formset,
        'estado_form': estado_form,
        'activo': activo,
        'historial': historial,
    })


@login_required
def eliminar_activo_view(request, pk):
    activo = get_object_or_404(Activo, pk=pk)

    if request.method == 'POST':
        estado_anterior = activo.estado
        activo.estado = 'baja'  # o 'eliminado' según tu lógica
        activo.save()

        EstadoHistorico.objects.create(
            activo=activo,
            estado_anterior=estado_anterior,
            estado_nuevo='baja',
            fecha_cambio=timezone.now()
        )

        messages.success(request, 'El activo fue marcado como dado de baja.')
        return redirect('listar_activos')

    messages.error(request, 'Acción no permitida.')
    return redirect('listar_activos')

@login_required
def importar_activos_view(request):
    if request.method == 'POST':
        form = ImportarExcelForm(request.POST, request.FILES)
        if form.is_valid():
            # Lógica de importación desde Excel
            messages.success(request, 'Importación completada.')
            return redirect('listar_activos')
    else:
        form = ImportarExcelForm()
    return render(request, 'importar_excel.html', {
        'form': form,
        'page_title': 'Importar Activos desde Excel'
    })

@login_required
def detalle_activo_view(request, pk):
    activo = get_object_or_404(Activo, pk=pk)
    switches = activo.switches.all()
    historial = EstadoHistorico.objects.filter(activo=activo).order_by('-fecha_cambio')

    estado_form = CambiarEstadoForm(instance=activo)

    return render(request, 'detalle_activo.html', {
        'activo': activo,
        'switches': switches,
        'historial': historial,
        'estado_form': estado_form
    })


from django.http import HttpResponseNotAllowed

def agregar_switch_a_activo(request, pk):
    return HttpResponseNotAllowed(['GET', 'POST'], 'Vista en construcción')


# def login_view(request):
#     if request.method == 'POST':
#         form = LdapLoginForm(request.POST)
#         if form.is_valid():
#             dni = form.cleaned_data['dni']
#             password = form.cleaned_data['password']

#             if LdapHelper.autenticar_ldap(dni, password):
#                 user, created = User.objects.get_or_create(username=dni)
#                 login(request, user)
#             return redirect('dashboard')
#         else:
#                     messages.error(request, "Credenciales inválidas.")
#     else:
#         form = LdapLoginForm()

#     return render(request, 'registration/login.html', {'form': form})
