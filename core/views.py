from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django import forms
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.models import User, Group, Permission
from django.http import HttpRequest, HttpResponse
from .models import Activo, FortiSwitch, EstadoActivo
from django.utils import timezone
from io import BytesIO
from openpyxl import Workbook
from django.template.loader import render_to_string
from weasyprint import HTML
from .forms import ActivoForm, FortiSwitchFormSet
# ---------- Auth ----------

class CustomLoginView(auth_views.LoginView):
    template_name = 'registration/login.html'  # si usás otro, ajustá acá


class CustomLogoutView(auth_views.LogoutView):
    next_page = 'login'


# ---------- Forms ----------

class ActivoForm(forms.ModelForm):
    class Meta:
        model = Activo
        fields = [
            'comando_region', 'titulo_abreviado', 'detalle_unidad',
            'modelo_equipo_fortinet', 'serie_fortinet', 'oblea_fortinet',
            'ospf', 'ip_admin', 'direccion_subred', 'red_dmz', 'red_wifi',
            'estado', 'grupo_admin_ldap', 'telefono_admin', 'apellido_nombre_admin',
            'observaciones'
        ]

class FortiSwitchForm(forms.ModelForm):
    class Meta:
        model = FortiSwitch
        fields = ['modelo_equipo', 'serie', 'oblea']

# ---------- Vistas ----------
@login_required
def dashboard_view(request):
    counts = Activo.objects.aggregate(
        total=Count('id'),
        activos=Count('id', filter=Q(estado='activo')),
        obs=Count('id', filter=Q(estado='observacion')),
        quem=Count('id', filter=Q(estado='quemado')),
        baja=Count('id', filter=Q(estado='baja')),
    )

    context = {
        'total_activos': counts['total'] or 0,
        'activos_activos': counts['activos'] or 0,
        'activos_observacion': counts['obs'] or 0,
        'activos_quemados': counts['quem'] or 0,
        'activos_baja': counts['baja'] or 0,
    }
    return render(request, 'dashboard.html', context)


@login_required
def listar_activos_view(request):
    estado = (request.GET.get('estado') or '').strip().lower()
    q = (request.GET.get('q') or '').strip()

    estados_validos = {'activo', 'observacion', 'quemado', 'baja'}

    qs = (Activo.objects
          .all()
          .prefetch_related('switches')
          .order_by('comando_region', 'titulo_abreviado'))

    if estado in estados_validos:
        qs = qs.filter(estado=estado)

    if q:
        qs = qs.filter(
            Q(comando_region__icontains=q) |
            Q(titulo_abreviado__icontains=q) |
            Q(modelo_equipo_fortinet__icontains=q) |
            Q(serie_fortinet__icontains=q) |
            Q(oblea_fortinet__icontains=q) |
            Q(ip_admin__icontains=q) |
            Q(direccion_subred__icontains=q) |
            Q(red_dmz__icontains=q) |
            Q(red_wifi__icontains=q) |
            Q(ospf__icontains=q) |
            Q(apellido_nombre_admin__icontains=q) |
            Q(grupo_admin_ldap__icontains=q) |
            Q(telefono_admin__icontains=q) |
            Q(switches__modelo_equipo__icontains=q) |
            Q(switches__serie__icontains=q) |
            Q(switches__oblea__icontains=q)
        ).distinct()  # evita duplicados por joins a switches

    counters = Activo.objects.aggregate(
        total=Count('id'),
        activos=Count('id', filter=Q(estado='activo')),
        obs=Count('id', filter=Q(estado='observacion')),
        quem=Count('id', filter=Q(estado='quemado')),
        baja=Count('id', filter=Q(estado='baja')),
    )

    context = {
        'activos': qs,
        'filtro_estado': estado if estado in estados_validos else '',
        'counters': counters,
        'q': q,  # para repoblar el input
    }
    return render(request, 'listado_activos.html', context)

@login_required
def crear_activo_view(request):
    if request.method == 'POST':
        form = ActivoForm(request.POST)
        formset = FortiSwitchFormSet(request.POST, prefix='switch')  # <- clave
        if form.is_valid() and formset.is_valid():
            activo = form.save()              # primero guardás el Activo
            formset.instance = activo         # enlazás el formset al Activo
            formset.save()
            messages.success(request, 'Activo creado correctamente.')
            return redirect('listar_activos')
    else:
        form = ActivoForm()
        formset = FortiSwitchFormSet(prefix='switch')  # <- clave

    return render(request, 'activo_form.html', {
        'form': form, 'formset': formset, 'page_title': 'Crear Activo'
    })


@login_required
def editar_activo_view(request, pk):
    activo = get_object_or_404(Activo, pk=pk)
    if request.method == 'POST':
        form = ActivoForm(request.POST, instance=activo)
        formset = FortiSwitchFormSet(request.POST, instance=activo, prefix='switch')  # <- clave
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, 'Activo actualizado correctamente.')
            return redirect('listar_activos')
    else:
        form = ActivoForm(instance=activo)
        formset = FortiSwitchFormSet(instance=activo, prefix='switch')  # <- clave

    return render(request, 'activo_form.html', {
        'form': form, 'formset': formset, 'page_title': 'Editar Activo'
    })

@login_required
def eliminar_activo_view(request, pk):
    activo = get_object_or_404(Activo, pk=pk)
    if request.method == 'POST':
        activo.delete()
        messages.success(request, "Activo eliminado.")
        return redirect('listar_activos')
    return render(request, 'activo_confirm_delete.html', {'activo': activo})


@login_required
def detalle_activo_view(request, pk):
    activo = get_object_or_404(Activo, pk=pk)
    switches = activo.switches.all()
    historial = activo.historial_estados.all().order_by('-fecha_cambio')
    return render(request, 'detalle_activo.html', {
        'activo': activo,
        'switches': switches,
        'historial': historial,
    })

@login_required
def agregar_switch_a_activo(request, pk):
    activo = get_object_or_404(Activo, pk=pk)
    if request.method == 'POST':
        form = FortiSwitchForm(request.POST)
        if form.is_valid():
            sw = form.save(commit=False)
            sw.activo = activo
            sw.save()
            messages.success(request, "Switch agregado al activo.")
            return redirect('detalle_activo', pk=pk)
    else:
        form = FortiSwitchForm(activo=activo)
    return render(request, 'agregar_switch.html', {'form': form, 'activo': activo})

@login_required
def importar_activos_view(request):
    """
    Vista stub para tu template importar_excel.html.
    Aquí luego podés procesar el archivo y crear registros.
    """
    if request.method == 'POST':
        # TODO: procesar request.FILES['archivo'] y crear activos
        messages.info(request, "Importación todavía no implementada.")
        return redirect('listar_activos')
    return render(request, 'importar_excel.html')


# --- Gestión de usuarios ---
@login_required
@permission_required('auth.view_user', raise_exception=True)
def gestionar_usuarios_view(request: HttpRequest) -> HttpResponse:
    """
    Lista simple de usuarios y sus grupos. Ajustá a tu template real.
    """
    usuarios = User.objects.select_related().all().order_by('username')
    grupos = Group.objects.all().order_by('name')
    ctx = {"usuarios": usuarios, "grupos": grupos}
    return render(request, "core/gestionar_usuarios.html", ctx)

@login_required
@permission_required('auth.view_permission', raise_exception=True)
def gestionar_roles_permisos_view(request: HttpRequest) -> HttpResponse:
    """
    Vista básica de roles (grupos) y permisos.
    """
    grupos = Group.objects.prefetch_related('permissions').order_by('name')
    permisos = Permission.objects.all().order_by('content_type__app_label', 'codename')
    ctx = {"grupos": grupos, "permisos": permisos}
    return render(request, "core/gestionar_roles_permisos.html", ctx)

@login_required
def importar_excel_view(request):
    if request.method == "POST":
        # TODO: procesar archivo
        return render(request, "importar_excel/resultado.html")
    return render(request, "importar_excel/form.html")


# ------------
ESTADOS_VALIDOS = {'activo', 'observacion', 'quemado', 'baja'}

def _build_queryset_from_request(request):
    estado = (request.GET.get('estado') or '').strip().lower()
    q = (request.GET.get('q') or '').strip()

    qs = (Activo.objects
          .all()
          .prefetch_related('switches')
          .order_by('comando_region', 'titulo_abreviado'))

    if estado in ESTADOS_VALIDOS:
        qs = qs.filter(estado=estado)

    if q:
        qs = qs.filter(
            Q(comando_region__icontains=q) |
            Q(titulo_abreviado__icontains=q) |
            Q(modelo_equipo_fortinet__icontains=q) |
            Q(serie_fortinet__icontains=q) |
            Q(oblea_fortinet__icontains=q) |
            Q(ip_admin__icontains=q) |
            Q(direccion_subred__icontains=q) |
            Q(red_dmz__icontains=q) |
            Q(red_wifi__icontains=q) |
            Q(ospf__icontains=q) |
            Q(apellido_nombre_admin__icontains=q) |
            Q(grupo_admin_ldap__icontains=q) |
            Q(telefono_admin__icontains=q) |
            Q(switches__modelo_equipo__icontains=q) |
            Q(switches__serie__icontains=q) |
            Q(switches__oblea__icontains=q)
        ).distinct()

    return qs, estado, q

def exportar_activos_excel(request):
    qs, estado, q = _build_queryset_from_request(request)

    wb = Workbook()
    ws = wb.active
    ws.title = "Activos"

    headers = [
        "Región", "Unidad",
        "Modelo Fortinet", "Serie Fortinet", "Oblea Fortinet",
        "Switches",   # concatenado
        "IP", "OSPF", "Subred", "DMZ", "WiFi",
        "Admin (Nombre)", "Teléfono", "LDAP",
        "Estado"
    ]
    ws.append(headers)

    for a in qs:
        sw_list = [f"{sw.modelo_equipo} / {sw.serie} / {sw.oblea or '-'}" for sw in a.switches.all()]
        switches_str = " | ".join(sw_list) if sw_list else "Sin switches"

        row = [
            a.comando_region,
            a.titulo_abreviado,
            a.modelo_equipo_fortinet,
            a.serie_fortinet,
            a.oblea_fortinet,
            switches_str,
            a.ip_admin,
            a.ospf,
            a.direccion_subred,
            a.red_dmz,
            a.red_wifi,
            a.apellido_nombre_admin,
            a.telefono_admin,
            a.grupo_admin_ldap,
            a.estado,
        ]
        ws.append(row)

    # (Opcional) ancho básico de columnas
    for col_cells in ws.columns:
        max_len = max((len(str(c.value)) if c.value else 0) for c in col_cells)
        col_letter = col_cells[0].column_letter
        ws.column_dimensions[col_letter].width = min(max(12, max_len + 2), 60)

    stream = BytesIO()
    wb.save(stream)
    stream.seek(0)

    ts = timezone.localtime().strftime("%Y%m%d_%H%M")
    filename = f"activos_{ts}.xlsx"
    response = HttpResponse(
        stream.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def exportar_activos_pdf(request):
    qs, estado, q = _build_queryset_from_request(request)

    context = {
        "activos": qs,
        "filtro_estado": estado,
        "q": q,
        "generado": timezone.localtime(),
    }
    html = render_to_string("reportes/activos_pdf.html", context, request=request)

    pdf_bytes = HTML(string=html, base_url=request.build_absolute_uri("/")).write_pdf()

    ts = timezone.localtime().strftime("%Y%m%d_%H%M")
    filename = f"activos_{ts}.pdf"
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response