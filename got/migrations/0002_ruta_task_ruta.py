# Generated by Django 5.0.1 on 2024-03-08 03:58

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('got', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Ruta',
            fields=[
                ('code', models.CharField(max_length=50, primary_key=True, serialize=False)),
                ('frecuency', models.IntegerField()),
                ('intervention_date', models.DateField()),
                ('system', models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='rutas', to='got.system')),
                ('ot', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='got.ot')),
                ('equipo', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='got.equipo')),
            ],
        ),
        migrations.AddField(
            model_name='task',
            name='ruta',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='got.ruta'),
        ),
        migrations.CreateModel(
            name='FailureReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('moment', models.DateTimeField(auto_now_add=True)),
                ('critico', models.BooleanField()),
                ('description', models.TextField()),
                ('causas', models.TextField()),
                ('suggest_repair', models.TextField(blank=True, null=True)),
                ('evidence', models.ImageField(blank=True, null=True, upload_to='media/')),
                ('equipo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='got.equipo')),
                ('reporter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
