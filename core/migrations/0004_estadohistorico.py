from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),  # Asegúrate de ajustar esta línea al nombre correcto de tu app
    ]

    operations = [
        migrations.CreateModel(
            name='EstadoHistorico',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('estado_anterior', models.CharField(blank=True, max_length=50, null=True)),
                ('estado_nuevo', models.CharField(max_length=50)),
                ('fecha_cambio', models.DateTimeField(default=django.utils.timezone.now)),
                ('activo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='historial_estados', to='core.activo')),
            ],
        ),
    ]