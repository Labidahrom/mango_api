# Generated by Django 5.0.1 on 2024-01-27 06:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mango_api', '0005_alter_operatorgolangversion_group'),
    ]

    operations = [
        migrations.AlterField(
            model_name='distributionschemagolangversion',
            name='id',
            field=models.IntegerField(primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='groupgolangversion',
            name='id',
            field=models.IntegerField(primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='operatorgolangversion',
            name='id',
            field=models.IntegerField(primary_key=True, serialize=False),
        ),
    ]
