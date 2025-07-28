from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib import messages
from .models import Activo, EstadoHistorico
from .forms import ActivoForm, ImportarExcelForm, FortiSwitchForm, FortiSwitchFormSet
from .forms import CambiarEstadoForm
import openpyxl

# Login personalizado
class CustomLoginView(LoginView):
    template_name = 'registration/login.html'

    def form_valid(self, form):
        messages.success(self.request, '¡Bienvenido!')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Credenciales inválidas.')
        return super().form_invalid(form)

# Logout personalizado
class CustomLogoutView(LogoutView):
    next_page = 'login'

    def dispatch(self, request, *args, **kwargs):
        messages.info(self.request, 'Sesión cerrada.')
        return super().dispatch(request, *args, **kwargs)

@login_required
def dashboard_view(request):
    total_activos = Activo.objects.count()
    return render(request, 'dashboard.html', {'total_activos': total_activos, 'page_title': 'Dashboard'})

@login_required
def lista_activos(request):
    activos = Activo.objects.all()
    return render(request, 'listado_activos.html', {'activos': activos, 'page_title': 'Listado de Activos'})

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
            EstadoHistorico.objects.create(activo=activo, estado=activo.estado, usuario=request.user)
            messages.success(request, 'Activo y switches creados correctamente.')
            return redirect('listado_activos')
        messages.error(request, 'Error en el formulario.')
    else:
        form = ActivoForm()
        formset = FortiSwitchFormSet(prefix='switch')
    return render(request, 'activo_form.html', {'form': form, 'formset': formset, 'page_title': 'Crear Nuevo Activo'})

from .models import EstadoHistorico

@login_required
def editar_activo_view(request, pk):
    activo = get_object_or_404(Activo, pk=pk)
    estado_original = activo.estado  # Guardamos el estado anterior

    if request.method == 'POST':
        form = ActivoForm(request.POST, instance=activo)
        formset = FortiSwitchFormSet(request.POST, queryset=activo.switches.all(), prefix='switch')

        if form.is_valid() and formset.is_valid():
            activo_actualizado = form.save()

            if estado_original != activo_actualizado.estado:
                EstadoHistorico.objects.create(
                    activo=activo,
                    estado_anterior=estado_original,
                    estado_nuevo=activo_actualizado.estado,
                )

            # Actualizar switches si usás formset
            switches = formset.save(commit=False)
            for sw in switches:
                sw.activo = activo
                sw.save()

            messages.success(request, 'Activo actualizado correctamente.')
            return redirect('listado_activos')
        else:
            messages.error(request, 'Error al actualizar el activo.')
    else:
        form = ActivoForm(instance=activo)
        formset = FortiSwitchFormSet(queryset=activo.switches.all(), prefix='switch')

    return render(request, 'activo_form.html', {
        'form': form,
        'formset': formset,
        'page_title': 'Editar Activo',
        'activo': activo,
    })


@login_required
def eliminar_activo_view(request, pk):
    activo = get_object_or_404(Activo, pk=pk)
    if request.method == 'POST':
        activo.delete()
        messages.success(request, 'Activo eliminado.')
    return redirect('listado_activos')

@login_required
def importar_activos_view(request):
    if request.method == 'POST':
        form = ImportarExcelForm(request.POST, request.FILES)
        if form.is_valid():
            archivo = request.FILES['archivo']
            wb = openpyxl.load_workbook(archivo)
            hoja = wb.active
            duplicados, incompletos, creados = [], [], 0
            for idx, fila in enumerate(hoja.iter_rows(min_row=2, values_only=True), start=2):
                ip_admin, serie = fila[7], fila[4]
                if not ip_admin or not serie:
                    incompletos.append(f"Fila {idx}")
                    continue
                if Activo.objects.filter(ip_admin=ip_admin).exists() or Activo.objects.filter(serie_fortinet=serie).exists():
                    duplicados.append(f"Fila {idx}")
                    continue
                Activo.objects.create(
                    comando_region=fila[0], titulo_abreviado=fila[1], detalle_unidad=fila[2],
                    modelo_equipo_fortinet=fila[3], serie_fortinet=serie, oblea_fortinet=fila[5],
                    ospf=fila[6], ip_admin=ip_admin, direccion_subred=fila[8], red_dmz=fila[9],
                    red_wifi=fila[10], grupo_admin_ldap=fila[11], apellido_nombre_admin=fila[12],
                    telefono_admin=fila[13], observaciones=fila[14], estado=fila[15]
                )
                creados += 1
            if creados: messages.success(request, f"{creados} activos importados.")
            if duplicados: messages.warning(request, f"Duplicados: {duplicados}")
            if incompletos: messages.error(request, f"Incompletos: {incompletos}")
            return redirect('listado_activos')
    else:
        form = ImportarExcelForm()
    return render(request, 'importar_excel.html', {'form': form, 'page_title': 'Importar desde Excel'})

@login_required
def detalle_activo_view(request, pk):
    activo = get_object_or_404(Activo, pk=pk)
    switches = activo.switches.all()
    historial = EstadoHistorico.objects.filter(activo=activo).order_by('-fecha_cambio')

    if request.method == 'POST':
        estado_form = CambiarEstadoForm(request.POST, instance=activo)
        if estado_form.is_valid():
            nuevo_estado = estado_form.cleaned_data['estado']
            if activo.estado != nuevo_estado:
                activo.estado = nuevo_estado
                activo.save()
                EstadoHistorico.objects.create(activo=activo, estado=nuevo_estado)
                messages.success(request, 'Estado actualizado correctamente.')
                return redirect('detalle_activo', pk=activo.pk)
    else:
        estado_form = CambiarEstadoForm(instance=activo)

    return render(request, 'detalle_activo.html', {
        'activo': activo,
        'switches': switches,
        'historial': historial,
        'estado_form': estado_form,
    })

@login_required
def agregar_switch_a_activo(request, pk):
    activo = get_object_or_404(Activo, pk=pk)
    if request.method == 'POST':
        form = FortiSwitchForm(request.POST)
        if form.is_valid():
            nuevo_switch = form.save(commit=False)
            nuevo_switch.activo = activo
            nuevo_switch.save()
            messages.success(request, 'Switch agregado correctamente.')
            return redirect('detalle_activo', pk=activo.pk)
    else:
        form = FortiSwitchForm()
    return render(request, 'agregar_switch.html', {'form': form, 'activo': activo, 'page_title': 'Agregar Switch'})
