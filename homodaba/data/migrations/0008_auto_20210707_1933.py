# Generated by Django 3.1 on 2021-07-07 19:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0007_imdbcache'),
    ]

    operations = [
        migrations.AddField(
            model_name='imdbcache',
            name='search_query',
            field=models.CharField(max_length=255, null=True, verbose_name='Search Query'),
        ),
        migrations.AlterField(
            model_name='imdbcache',
            name='raw_data',
            field=models.TextField(blank=True, null=True, verbose_name='Raw Data'),
        ),
    ]
