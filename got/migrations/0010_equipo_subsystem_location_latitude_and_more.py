# Generated by Django 5.0.1 on 2024-06-02 13:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('got', '0009_alter_task_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='equipo',
            name='subsystem',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='location',
            name='latitude',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
        ),
        migrations.AddField(
            model_name='location',
            name='longitude',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
        ),
        migrations.AlterField(
            model_name='location',
            name='contact',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='location',
            name='num_contact',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.DeleteModel(
            name='Component',
        ),
    ]