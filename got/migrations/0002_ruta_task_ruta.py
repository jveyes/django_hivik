# Generated by Django 5.0.1 on 2024-03-08 03:58

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
import got.models
import simple_history.models


class Migration(migrations.Migration):

    dependencies = [
        ('got', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Ruta',
            fields=[
                ('code', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=50)),
                ('frecuency', models.IntegerField()),
                ('intervention_date', models.DateField()),
                ('system', models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='rutas', to='got.system')),
                ('ot', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='got.ot')),
                ('equipo', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='got.equipo')),
                ('control', models.CharField(choices=[('d', 'Días'), ('h', 'Horas')], max_length=1))
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
                ('evidence', models.ImageField(blank=True, null=True, upload_to=got.models.get_upload_path)),
                ('equipo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='got.equipo')),
                ('reporter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('related_ot', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='failure_report', to='got.ot')),
                ('closed', models.BooleanField(default=False)),
            ],
            options={'ordering': ['-moment']},
        ),
        migrations.AddField(
            model_name='equipo',
            name='tipo',
            field=models.CharField(choices=[('r', 'Rotativo'), ('nr', 'No rotativo')], default='nr', max_length=2),
        ),
        migrations.CreateModel(
            name='HistoryHour',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('report_date', models.DateField()),
                ('hour', models.DecimalField(decimal_places=2, max_digits=5)),
                ('component', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='hours', to='got.equipo')),
                ('reporter', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-report_date'],
            },
        ),
        migrations.CreateModel(
            name='HistoricalSystem',
            fields=[
                ('id', models.BigIntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('group', models.IntegerField()),
                ('location', models.CharField(blank=True, default='Cartagena', max_length=50, null=True)),
                ('state', models.CharField(choices=[('m', 'Mantenimiento'), ('o', 'Operativo'), ('x', 'Fuera de servicio')], default='m', max_length=1)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('asset', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='got.asset')),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'historical system',
                'verbose_name_plural': 'historical systems',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
                migrations.CreateModel(
            name='HistoricalFailureReport',
            fields=[
                ('id', models.BigIntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('moment', models.DateTimeField(blank=True, editable=False)),
                ('description', models.TextField()),
                ('causas', models.TextField()),
                ('suggest_repair', models.TextField(blank=True, null=True)),
                ('critico', models.BooleanField()),
                ('evidence', models.TextField(blank=True, max_length=100, null=True)),
                ('closed', models.BooleanField(default=False)),
                ('impact', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(choices=[('s', 'La seguridad personal'), ('m', 'El medio ambiente'), ('i', 'Integridad del equipo/sistema'), ('o', 'El desarrollo normal de las operaciones')], max_length=1), blank=True, default=list, size=None)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('equipo', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='got.equipo')),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('related_ot', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='got.ot')),
                ('reporter', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'historical failure report',
                'verbose_name_plural': 'historical failure reports',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='HistoricalOt',
            fields=[
                ('creation_date', models.DateField(blank=True, editable=False)),
                ('num_ot', models.IntegerField(blank=True, db_index=True)),
                ('description', models.TextField()),
                ('state', models.CharField(choices=[('a', 'Abierto'), ('x', 'En ejecucion'), ('f', 'Finalizado'), ('c', 'Cancelado')], default='x', max_length=50)),
                ('tipo_mtto', models.CharField(choices=[('p', 'Preventivo'), ('c', 'Correctivo'), ('m', 'Modificativo')], max_length=1)),
                ('info_contratista_pdf', models.TextField(blank=True, max_length=100, null=True)),
                ('ot_aprobada', models.TextField(blank=True, max_length=100, null=True)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('super', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('system', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='got.system')),
            ],
            options={
                'verbose_name': 'historical ot',
                'verbose_name_plural': 'historical ots',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='HistoricalRuta',
            fields=[
                ('code', models.IntegerField(blank=True, db_index=True)),
                ('name', models.CharField(max_length=50)),
                ('control', models.CharField(choices=[('d', 'Días'), ('h', 'Horas')], max_length=1)),
                ('frecuency', models.IntegerField()),
                ('intervention_date', models.DateField()),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('dependencia', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='got.ruta')),
                ('equipo', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='got.equipo')),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('ot', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='got.ot')),
                ('system', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='got.system')),
            ],
            options={
                'verbose_name': 'historical ruta',
                'verbose_name_plural': 'historical rutas',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='HistoricalTask',
            fields=[
                ('id', models.BigIntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('description', models.TextField()),
                ('procedimiento', models.TextField(blank=True, default='', null=True)),
                ('hse', models.TextField(blank=True, default='', null=True)),
                ('suministros', models.TextField(blank=True, default='', null=True)),
                ('news', models.TextField(blank=True, null=True)),
                ('evidence', models.TextField(blank=True, max_length=100, null=True)),
                ('start_date', models.DateField(blank=True, null=True)),
                ('men_time', models.IntegerField(default=0)),
                ('finished', models.BooleanField()),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('ot', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='got.ot')),
                ('responsible', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('ruta', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='got.ruta')),
            ],
            options={
                'verbose_name': 'historical task',
                'verbose_name_plural': 'historical tasks',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
    ]
