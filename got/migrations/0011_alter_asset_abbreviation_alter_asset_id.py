# Archivo: got/migrations/0011_alter_asset_abbreviation_alter_asset_id.py
from django.db import migrations, models, connection


def update_foreign_keys(apps, schema_editor):
    with connection.cursor() as cursor:
        # Actualiza los registros del modelo System
        cursor.execute('''
            UPDATE got_system s
            SET asset_id = a.abbreviation
            FROM got_asset a
            WHERE a.id = s.asset_id::integer
        ''')


class Migration(migrations.Migration):

    dependencies = [
        ('got', '0010_asset_id_delete_historicalsystem'),
    ]

    operations = [
        migrations.AlterField(
            model_name='system',
            name='asset',
            field=models.ForeignKey(to='got.Asset', on_delete=models.CASCADE, db_column='asset_id', to_field='abbreviation'),
        ),
        migrations.RunPython(update_foreign_keys),
    ]
