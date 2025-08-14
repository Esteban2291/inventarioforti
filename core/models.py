from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator
from django.db.models import TextChoices
from django.core.exceptions import ValidationError
from django.urls import reverse


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

    # Unicidad global (case-insensitive por collation)
    serie_fortinet = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Serie (Fortinet)",
    )
    # Única si tiene valor (case-insensitive por collation)
    oblea_fortinet = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        verbose_name="Oblea (Fortinet)",
    )

    # Red
    ospf = models.CharField(max_length=20, blank=True, null=True, verbose_name="OSPF")
    ip_admin = models.GenericIPAddressField(protocol='IPv4', unique=True, verbose_name="IP Admin")
    direccion_subred = models.CharField(max_length=50, blank=True, null=True, verbose_name="Dirección Subred")
    red_dmz = models.CharField(max_length=50, blank=True, null=True, verbose_name="Red DMZ")
    red_wifi = models.CharField(max_length=50, blank=True, null=True, verbose_name="Red WiFi")

    # Estado
    estado = models.CharField(
        max_length=20,
        choices=EstadoActivo.choices,
        default=EstadoActivo.ACTIVO,
        verbose_name="Estado del Activo",
        db_index=True,
    )

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
        # ⬆️ No hace falta UniqueConstraint con Lower(): la collation ya da case-insensitive.

    def __str__(self):
        return f"{self.comando_region} - {self.ip_admin}"

    def get_absolute_url(self):
        return reverse('detalle_activo', args=[self.pk])

    def clean(self):
        """Evita que la oblea de FortiGate se repita en un FortiSwitch."""
        super().clean()
        if self.oblea_fortinet:
            from .models import FortiSwitch
            if FortiSwitch.objects.filter(oblea__iexact=self.oblea_fortinet).exists():
                raise ValidationError({'oblea_fortinet': 'Esta oblea ya está usada por un FortiSwitch.'})

    def save(self, *args, **kwargs):
        # Registrar histórico si cambia el estado
        if self.pk:
            anterior = Activo.objects.filter(pk=self.pk).only('estado').first()
            super().save(*args, **kwargs)
            if anterior and anterior.estado != self.estado:
                EstadoHistorico.objects.create(
                    activo=self,
                    estado_anterior=anterior.estado,
                    estado_nuevo=self.estado,
                )
        else:
            super().save(*args, **kwargs)


class FortiSwitch(models.Model):
    MODELO_CHOICES = (
        ('FortiSwitch 224E', 'FortiSwitch 224E'),
        ('FortiSwitch 248E', 'FortiSwitch 248E'),
    )

    modelo_equipo = models.CharField(
        max_length=100,
        choices=MODELO_CHOICES,
        db_index=True,
        verbose_name="Modelo del Switch",
    )

    # Unicidad global (case-insensitive por collation)
    serie = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Serie (Switch)",
    )
    # Única si tiene valor (case-insensitive por collation)
    oblea = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
        verbose_name="Oblea (Switch)",
    )

    activo = models.ForeignKey('Activo', related_name='switches', on_delete=models.CASCADE)

    class Meta:
        ordering = ['activo_id', 'modelo_equipo', 'serie']
        indexes = [
            models.Index(fields=['modelo_equipo']),
            # No agregamos index extra para 'serie' porque el UNIQUE ya crea índice.
        ]

    def __str__(self):
        return f"{self.modelo_equipo} - {self.serie} ({self.activo.ip_admin})"

    def clean(self):
        """Evita oblea duplicada entre Switch y FortiGate."""
        super().clean()
        if self.oblea:
            from .models import Activo
            if Activo.objects.filter(oblea_fortinet__iexact=self.oblea).exists():
                raise ValidationError({'oblea': 'Esta oblea ya está usada por un FortiGate.'})


class EstadoHistorico(models.Model):
    activo = models.ForeignKey('Activo', on_delete=models.CASCADE, related_name='historial_estados')
    estado_anterior = models.CharField(max_length=50, blank=True, null=True)
    estado_nuevo = models.CharField(max_length=50)
    fecha_cambio = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.activo} - {self.estado_anterior} → {self.estado_nuevo}"
