# Generated by Django 5.0.1 on 2024-03-09 13:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('got', '0005_alter_ruta_system'),
    ]

    operations = [
        migrations.AddField(
            model_name='equipo',
            name='manual_pdf',
            field=models.FileField(blank=True, null=True, upload_to='pdfs/'),
        ),
    ]