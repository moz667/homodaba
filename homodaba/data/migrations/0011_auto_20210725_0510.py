# Generated by Django 3.1 on 2021-07-25 05:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0010_auto_20210725_0409'),
    ]

    operations = [
        migrations.AlterField(
            model_name='moviestoragetype',
            name='media_format',
            field=models.CharField(choices=[('', 'Otro'), ('UNKNOWN', 'Desconocido'), ('AVI', 'AVI'), ('BLURAY', 'BLURAY'), ('BLURAY-ISO', 'BLURAY-ISO'), ('DVD', 'DVD'), ('DVD-ISO', 'DVD-ISO'), ('ISO', 'ISO'), ('M2TS', 'M2TS'), ('M4V', 'M4V'), ('MKV', 'MKV'), ('MP4', 'MP4'), ('ULTRA-BLURAY', 'ULTRA-BLURAY')], default='DVD', max_length=20, verbose_name='Formato'),
        ),
    ]
