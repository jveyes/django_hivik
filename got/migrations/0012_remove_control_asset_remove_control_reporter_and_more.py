# Generated by Django 5.0.1 on 2024-07-04 01:16

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('got', '0011_alter_ruta_dependencia'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveField(
            model_name='control',
            name='asset',
        ),
        migrations.RemoveField(
            model_name='control',
            name='reporter',
        ),
        migrations.AlterUniqueTogether(
            name='stock',
            unique_together=None,
        ),
        migrations.RemoveField(
            model_name='stock',
            name='asset',
        ),
        migrations.RemoveField(
            model_name='stock',
            name='item',
        ),
        migrations.RemoveField(
            model_name='solicitud',
            name='seccion',
        ),
        migrations.AddField(
            model_name='suministro',
            name='asset',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='suministros', to='got.asset'),
        ),
        migrations.CreateModel(
            name='TransaccionSuministro',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cantidad_ingresada', models.IntegerField(default=0, help_text='Cantidad que se añade al inventario')),
                ('cantidad_consumida', models.IntegerField(default=0, help_text='Cantidad que se consume del inventario')),
                ('fecha', models.DateTimeField(auto_now_add=True)),
                ('suministro', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transacciones', to='got.suministro')),
                ('usuario', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.DeleteModel(
            name='Consumibles',
        ),
        migrations.DeleteModel(
            name='Control',
        ),
        migrations.DeleteModel(
            name='Stock',
        ),
    ]