# Generated by Django 5.0.1 on 2024-03-01 06:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mango_api', '0009_alter_callhistorygolangversion_entry_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='callhistorygolangversion',
            name='recording_id',
            field=models.CharField(max_length=300, null=True),
        ),
    ]