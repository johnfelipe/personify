# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-09-07 11:15
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('personify', '0009_profile_friends'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='friend_ids_cache',
            field=jsonfield.fields.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='profile',
            name='friends',
            field=models.ManyToManyField(blank=True, related_name='_profile_friends_+', to='personify.Profile'),
        ),
    ]
