from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator
from django.db.models import TextChoices

class EstadoActivo(TextChoices):
    ACTIVO = 'activo', 'Activo'
    OBSERVACION = 'observacion', 'En observación'
    QUEMADO = 'quemado', 'Quemado'
    BAJA = 'baja', 'Dado de baja'

class Activo(models.Model):
    # Equipo
    comando_region = models.CharField(max_length=100, verbose_name="Región", db_index=True)
    titulo_abreviado = models.CharField(max_length=50, verbose_name="Título Abreviado")
    detalle_unidad = models.CharField(max_length=200, verbose_name="Detalle de la Unidad", blank=True, null=True)
    modelo_equipo_fortinet = models.CharField(max_length=100, verbose_name="Modelo Equipo (Fortinet)", db_index=True)
    serie_fortinet = models.CharField(max_length=100, unique=True, verbose_name="Serie (Fortinet)")
    oblea_fortinet = models.CharField(max_length=50, blank=True, null=True, verbose_name="Oblea (Fortinet)")

    # Red
    ospf = models.CharField(max_length=20, blank=True, null=True, verbose_name="OSPF")
    ip_admin = models.GenericIPAddressField(protocol='IPv4', unique=True, verbose_name="IP Admin")
    direccion_subred = models.CharField(max_length=50, blank=True, null=True, verbose_name="Dirección Subred")
    red_dmz = models.CharField(max_length=50, blank=True, null=True, verbose_name="Red DMZ")
    red_wifi = models.CharField(max_length=50, blank=True, null=True, verbose_name="Red WiFi")

    # Estado
    estado = models.CharField(max_length=20, choices=EstadoActivo.choices, default=EstadoActivo.ACTIVO, verbose_name="Estado del Activo", db_index=True)

    # Admin Unidad
    grupo_admin_ldap = models.CharField(max_length=100, blank=True, null=True, verbose_name="Grupo Admin LDAP")
    telefono_admin = models.CharField(
        max_length=20, blank=True, null=True, verbose_name="Teléfono (Admin Unidad)",
        validators=[RegexValidator(r'^[\d\-\+\s\(\)]+$')]
    )
    apellido_nombre_admin = models.CharField(max_length=100, verbose_name="Apellido y Nombre (Admin Unidad)")

    observaciones = models.TextField(blank=True, null=True, verbose_name="Observaciones")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Activo de Red"
        verbose_name_plural = "Activos de Red"
        ordering = ['comando_region', 'ip_admin']
        indexes = [
            models.Index(fields=['comando_region']),
            models.Index(fields=['estado']),
            models.Index(fields=['modelo_equipo_fortinet']),
        ]

    def __str__(self):
        return f"{self.comando_region} - {self.ip_admin}"

class FortiSwitch(models.Model):
    modelo_equipo = models.CharField(max_length=100)
    serie = models.CharField(max_length=100, unique=True, db_index=True)
    oblea = models.CharField(max_length=100, blank=True, null=True)
    activo = models.ForeignKey('Activo', related_name='switches', on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.modelo_equipo} - {self.serie} ({self.activo.ip_admin})"

class EstadoHistorico(models.Model):
    activo = models.ForeignKey('Activo', on_delete=models.CASCADE, related_name='historial_estados')
    estado_anterior = models.CharField(max_length=50, blank=True, null=True)
    estado_nuevo = models.CharField(max_length=50)
    fecha_cambio = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.activo} - {self.estado_anterior} → {self.estado_nuevo}"
