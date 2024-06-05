# Generated by Django 5.0.1 on 2024-06-05 01:03

import django.db.models.deletion
import got.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('got', '0010_equipo_subsystem_location_latitude_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='location',
            name='latitude',
            field=models.DecimalField(blank=True, decimal_places=20, max_digits=20, null=True),
        ),
        migrations.AlterField(
            model_name='location',
            name='longitude',
            field=models.DecimalField(blank=True, decimal_places=20, max_digits=20, null=True),
        ),
        migrations.CreateModel(
            name='Document',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to=got.models.get_upload_pdfs)),
                ('description', models.CharField(max_length=200)),
                ('asset', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='documents', to='got.asset')),
            ],
        ),
        migrations.DeleteModel(
            name='Megger',
        ),
    ]
