# Generated by Django 5.0.1 on 2024-02-29 03:27

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Component',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('code', models.CharField(max_length=50)),
                ('location_int', models.CharField(blank=True, max_length=50, null=True)),
                ('area', models.CharField(blank=True, default='null', max_length=50, null=True)),
                ('model', models.CharField(blank=True, default='null', max_length=50, null=True)),
                ('serial', models.CharField(blank=True, default='null', max_length=50, null=True)),
                ('marca', models.CharField(blank=True, default='null', max_length=50, null=True)),
                ('fabricante', models.CharField(blank=True, default='null', max_length=50, null=True)),
                ('feature', models.TextField(default='null')),
                ('state', models.CharField(choices=[('m', 'Mantenimiento'), ('o', 'Operativo'), ('x', 'Fuera de servicio')], default='m')),
            ],
            options={
                'ordering': ['name', 'code'],
            },
        ),
        migrations.CreateModel(
            name='Asset',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('location', models.CharField(max_length=50)),
                ('state', models.CharField(choices=[('m', 'Mantenimiento'), ('o', 'Operacion'), ('d', 'Dique'), ('x', 'Fuera de servicio')], default='m')),
                ('supervisor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'permissions': (('can_see_completely', 'Access to completely info'),),
            },
        ),
        migrations.CreateModel(
            name='Ruta',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('frecuency', models.IntegerField()),
                ('component', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='got.component')),
            ],
        ),
        migrations.CreateModel(
            name='System',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('gruop', models.IntegerField()),
                ('asset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='got.asset')),
            ],
            options={
                'ordering': ['asset__name', 'gruop'],
            },
        ),
        migrations.CreateModel(
            name='Ot',
            fields=[
                ('creation_date', models.DateField(auto_now=True)),
                ('num_ot', models.AutoField(primary_key=True, serialize=False)),
                ('description', models.TextField()),
                ('state', models.CharField(choices=[('a', 'Abierto'), ('x', 'En ejecucion'), ('f', 'Finalizado'), ('c', 'Cancelado')], default='a')),
                ('super', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('system', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='got.system')),
            ],
        ),
        migrations.AddField(
            model_name='component',
            name='system',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='got.system'),
        ),
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.TextField()),
                ('news', models.TextField(blank=True, null=True)),
                ('evidence', models.ImageField(blank=True, null=True, upload_to='evidencias')),
                ('start_date', models.DateField()),
                ('men_time', models.IntegerField(default=1)),
                ('finished', models.BooleanField()),
                ('ot', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='got.ot')),
                ('responsible', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('ruta', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='got.ruta')),
            ],
        ),
    ]
