# Generated by Django 5.0.1 on 2024-01-25 05:26

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CallHistoryGolangVersion',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('entry_id', models.CharField(max_length=50)),
                ('napravlenie', models.CharField(max_length=50)),
                ('data_postupil', models.DateField(null=True)),
                ('time_postupil', models.TimeField(null=True)),
                ('gruppa', models.CharField(max_length=100, null=True)),
                ('dlitelnost', models.CharField(max_length=10, null=True)),
                ('tel_kto_zvonil', models.CharField(max_length=100, null=True)),
                ('komu_zvonil', models.CharField(max_length=100, null=True)),
                ('tel_komu_zvonil', models.CharField(max_length=100, null=True)),
                ('kuda_zvonil', models.CharField(max_length=100, null=True)),
                ('komment_k_nomeru', models.CharField(max_length=100, null=True)),
                ('data_okonchania_razgovora', models.DateField(null=True)),
                ('time_okonchania_razgovora', models.TimeField(null=True)),
                ('recording_id', models.CharField(max_length=60, null=True)),
            ],
            options={
                'db_table': 'call_history_golang_version',
            },
        ),
        migrations.CreateModel(
            name='DistributionSchemaGolangVersion',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100, null=True)),
                ('description', models.CharField(blank=True, max_length=100, null=True)),
            ],
            options={
                'db_table': 'distribution_schema_golang_version',
            },
        ),
        migrations.CreateModel(
            name='GroupGolangVersion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
            ],
            options={
                'db_table': 'group_golang_version',
            },
        ),
        migrations.CreateModel(
            name='OperatorGolangVersion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=100, null=True)),
                ('group', models.CharField(blank=True, max_length=100, null=True)),
                ('telegram_id', models.BigIntegerField(blank=True, null=True)),
            ],
            options={
                'db_table': 'operator_golang_version',
            },
        ),
        migrations.CreateModel(
            name='PhoneGolangVersion',
            fields=[
                ('number', models.CharField(max_length=100, primary_key=True, serialize=False)),
                ('comment', models.CharField(blank=True, max_length=100, null=True)),
                ('schema_id', models.IntegerField()),
            ],
            options={
                'db_table': 'phone_golang_version',
            },
        ),
        migrations.CreateModel(
            name='CallRecordingGolangVersion',
            fields=[
                ('id', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='recordings', serialize=False, to='mango_api.callhistorygolangversion')),
                ('date', models.DateField(null=True)),
                ('recording', models.BinaryField(null=True)),
            ],
            options={
                'db_table': 'call_recording_golang_version',
            },
        ),
    ]
