# Generated by Django 5.0.1 on 2024-05-27 04:19

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('got', '0006_delete_megger'),
    ]

    operations = [
        migrations.CreateModel(
            name='Megger',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha', models.DateField()),
                ('estator_pi_1min_l1_tierra', models.DecimalField(decimal_places=2, max_digits=5)),
                ('estator_pi_1min_l2_tierra', models.DecimalField(decimal_places=2, max_digits=5)),
                ('estator_pi_1min_l3_tierra', models.DecimalField(decimal_places=2, max_digits=5)),
                ('estator_pi_1min_l1_l2', models.DecimalField(decimal_places=2, max_digits=5)),
                ('estator_pi_1min_l2_l3', models.DecimalField(decimal_places=2, max_digits=5)),
                ('estator_pi_1min_l3_l1', models.DecimalField(decimal_places=2, max_digits=5)),
                ('estator_pi_10min_l1_tierra', models.DecimalField(decimal_places=2, max_digits=5)),
                ('estator_pi_10min_l2_tierra', models.DecimalField(decimal_places=2, max_digits=5)),
                ('estator_pi_10min_l3_tierra', models.DecimalField(decimal_places=2, max_digits=5)),
                ('estator_pi_10min_l1_l2', models.DecimalField(decimal_places=2, max_digits=5)),
                ('estator_pi_10min_l2_l3', models.DecimalField(decimal_places=2, max_digits=5)),
                ('estator_pi_10min_l3_l1', models.DecimalField(decimal_places=2, max_digits=5)),
                ('estator_pi_obs_l1_tierra', models.DecimalField(decimal_places=2, max_digits=5)),
                ('estator_pi_obs_l2_tierra', models.DecimalField(decimal_places=2, max_digits=5)),
                ('estator_pi_obs_l3_tierra', models.DecimalField(decimal_places=2, max_digits=5)),
                ('estator_pi_obs_l1_l2', models.DecimalField(decimal_places=2, max_digits=5)),
                ('estator_pi_obs_l2_l3', models.DecimalField(decimal_places=2, max_digits=5)),
                ('estator_pi_obs_l3_l1', models.DecimalField(decimal_places=2, max_digits=5)),
                ('estator_pf_1min_l1_tierra', models.DecimalField(decimal_places=2, max_digits=5)),
                ('estator_pf_1min_l2_tierra', models.DecimalField(decimal_places=2, max_digits=5)),
                ('estator_pf_1min_l3_tierra', models.DecimalField(decimal_places=2, max_digits=5)),
                ('estator_pf_1min_l1_l2', models.DecimalField(decimal_places=2, max_digits=5)),
                ('estator_pf_1min_l2_l3', models.DecimalField(decimal_places=2, max_digits=5)),
                ('estator_pf_1min_l3_l1', models.DecimalField(decimal_places=2, max_digits=5)),
                ('estator_pf_10min_l1_tierra', models.DecimalField(decimal_places=2, max_digits=5)),
                ('estator_pf_10min_l2_tierra', models.DecimalField(decimal_places=2, max_digits=5)),
                ('estator_pf_10min_l3_tierra', models.DecimalField(decimal_places=2, max_digits=5)),
                ('estator_pf_10min_l1_l2', models.DecimalField(decimal_places=2, max_digits=5)),
                ('estator_pf_10min_l2_l3', models.DecimalField(decimal_places=2, max_digits=5)),
                ('estator_pf_10min_l3_l1', models.DecimalField(decimal_places=2, max_digits=5)),
                ('estator_pf_obs_l1_tierra', models.DecimalField(decimal_places=2, max_digits=5)),
                ('estator_pf_obs_l2_tierra', models.DecimalField(decimal_places=2, max_digits=5)),
                ('estator_pf_obs_l3_tierra', models.DecimalField(decimal_places=2, max_digits=5)),
                ('estator_pf_obs_l1_l2', models.DecimalField(decimal_places=2, max_digits=5)),
                ('estator_pf_obs_l2_l3', models.DecimalField(decimal_places=2, max_digits=5)),
                ('estator_pf_obs_l3_l1', models.DecimalField(decimal_places=2, max_digits=5)),
                ('excitatriz_pi_1min_l_tierra', models.DecimalField(decimal_places=2, max_digits=5)),
                ('excitatriz_pi_10min_l_tierra', models.DecimalField(decimal_places=2, max_digits=5)),
                ('excitatriz_pi_obs_l_tierra', models.DecimalField(decimal_places=2, max_digits=5)),
                ('excitatriz_pf_1min_l_tierra', models.DecimalField(decimal_places=2, max_digits=5)),
                ('excitatriz_pf_10min_l_tierra', models.DecimalField(decimal_places=2, max_digits=5)),
                ('excitatriz_pf_obs_l_tierra', models.DecimalField(decimal_places=2, max_digits=5)),
                ('rotor_p_pi_1min_l_tierra', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('rotor_p_pi_10min_l_tierra', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('rotor_p_pi_obs_l_tierra', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('rotor_p_pf_1min_l_tierra', models.DecimalField(decimal_places=2, max_digits=5)),
                ('rotor_p_pf_10min_l_tierra', models.DecimalField(decimal_places=2, max_digits=5)),
                ('rotor_p_pf_obs_l_tierra', models.DecimalField(decimal_places=2, max_digits=5)),
                ('rotor_aux_pi_1min_l_tierra', models.DecimalField(decimal_places=2, max_digits=5)),
                ('rotor_aux_pi_10min_l_tierra', models.DecimalField(decimal_places=2, max_digits=5)),
                ('rotor_aux_pi_obs_l_tierra', models.DecimalField(decimal_places=2, max_digits=5)),
                ('rotor_aux_pf_1min_l_tierra', models.DecimalField(decimal_places=2, max_digits=5)),
                ('rotor_aux_pf_10min_l_tierra', models.DecimalField(decimal_places=2, max_digits=5)),
                ('rotor_aux_pf_obs_l_tierra', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('equipo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='got.equipo')),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='got.task')),
            ],
        ),
    ]
