# Generated by Django 5.0.1 on 2024-03-16 14:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('got', '0010_alter_equipo_initial_hours'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='hse',
            field=models.TextField(blank=True, default='---', null=True),
        ),
        migrations.AddField(
            model_name='task',
            name='procedimiento',
            field=models.TextField(blank=True, default='---', null=True),
        ),
        migrations.AddField(
            model_name='task',
            name='suministros',
            field=models.TextField(blank=True, default='---', null=True),
        ),
    ]
