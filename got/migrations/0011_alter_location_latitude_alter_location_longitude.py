# Generated by Django 5.0.1 on 2024-06-04 03:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('got', '0010_equipo_subsystem_location_latitude_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='location',
            name='latitude',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=20, null=True),
        ),
        migrations.AlterField(
            model_name='location',
            name='longitude',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=20, null=True),
        ),
    ]