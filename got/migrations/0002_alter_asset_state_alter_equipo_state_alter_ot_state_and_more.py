# Generated by Django 5.0.1 on 2024-03-02 23:15

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('got', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='asset',
            name='state',
            field=models.CharField(choices=[('m', 'Mantenimiento'), ('o', 'Operacion'), ('d', 'Dique'), ('x', 'Fuera de servicio')], default='m', max_length=50),
        ),
        migrations.AlterField(
            model_name='equipo',
            name='state',
            field=models.CharField(choices=[('m', 'Mantenimiento'), ('o', 'Operativo'), ('x', 'Fuera de servicio')], max_length=50),
        ),
        migrations.AlterField(
            model_name='ot',
            name='state',
            field=models.CharField(choices=[('a', 'Abierto'), ('x', 'En ejecucion'), ('f', 'Finalizado'), ('c', 'Cancelado')], default='a', max_length=50),
        ),
        migrations.AlterField(
            model_name='task',
            name='evidence',
            field=models.ImageField(blank=True, null=True, upload_to='media/'),
        ),
        migrations.CreateModel(
            name='Ruta',
            fields=[
                ('name', models.CharField(max_length=50)),
                ('frecuency', models.IntegerField()),
                ('code', models.CharField(max_length=50, primary_key=True, serialize=False)),
                ('intervention_date', models.DateField()),
                ('component', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='got.equipo')),
            ],
        ),
        migrations.DeleteModel(
            name='Rut',
        ),
    ]
