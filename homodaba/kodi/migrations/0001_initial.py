# Generated by Django 3.1 on 2021-08-11 15:59

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='KodiHost',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('host_url', models.CharField(max_length=255, verbose_name='Host URL')),
                ('login_username', models.CharField(default='kodi', max_length=50, verbose_name='Nombre de usuario')),
                ('login_password', models.CharField(blank=True, max_length=50, null=True, verbose_name='Contraseña')),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='propietario')),
            ],
        ),
    ]
