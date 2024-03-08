# Generated by Django 5.0.1 on 2024-03-08 03:58

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('got', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Ruta',
            fields=[
                ('code', models.CharField(max_length=50, primary_key=True, serialize=False)),
                ('frecuency', models.IntegerField()),
                ('intervention_date', models.DateField()),
                ('system', models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='rutas', to='got.system')),
            ],
        ),
        migrations.AddField(
            model_name='task',
            name='ruta',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='got.ruta'),
        ),
    ]
