# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-09-04 20:56
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('personify', '0007_auto_20160904_1750'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='share_key',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
