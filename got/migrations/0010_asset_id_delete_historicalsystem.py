# Generated by Django 5.0.1 on 2024-05-07 05:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('got', '0009_remove_asset_id_alter_asset_abbreviation'),
    ]

    operations = [
        migrations.AddField(
            model_name='asset',
            name='id',
            field=models.IntegerField(default=0),
        ),
        migrations.DeleteModel(
            name='HistoricalSystem',
        ),
    ]
