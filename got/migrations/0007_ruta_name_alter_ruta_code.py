# Generated by Django 5.0.1 on 2024-03-09 14:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('got', '0006_equipo_manual_pdf'),
    ]

    operations = [
        migrations.AddField(
            model_name='ruta',
            name='name',
            field=models.CharField(max_length=50),
        ),
        migrations.AlterField(
            model_name='ruta',
            name='code',
            field=models.AutoField(primary_key=True, serialize=False),
        ),
    ]
