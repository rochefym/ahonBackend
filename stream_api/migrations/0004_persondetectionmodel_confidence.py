# Generated by Django 5.0.3 on 2025-07-17 20:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stream_api', '0003_persondetectionmodel_is_selected'),
    ]

    operations = [
        migrations.AddField(
            model_name='persondetectionmodel',
            name='confidence',
            field=models.FloatField(default=0.5),
        ),
    ]
