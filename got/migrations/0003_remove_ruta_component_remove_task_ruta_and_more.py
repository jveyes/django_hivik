# Generated by Django 5.0.1 on 2024-02-29 15:42

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('got', '0002_remove_component_id_component_date_inv_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ruta',
            name='component',
        ),
        migrations.RemoveField(
            model_name='task',
            name='ruta',
        ),
        migrations.DeleteModel(
            name='Component',
        ),
        migrations.DeleteModel(
            name='Ruta',
        ),
    ]