# Generated by Django 3.1 on 2021-07-03 21:26

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0005_person_movies_as_director'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='person',
            name='movies_as_director',
        ),
    ]