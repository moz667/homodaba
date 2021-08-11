from django.db import models
from django.contrib.auth.models import User

class KodiHost(models.Model):
    host_name = models.CharField('Nombre', max_length=255, null=False, blank=False, help_text="De caracter identificativo (Dormitorio, Salon...)")
    host_url = models.CharField('Host URL', max_length=255, null=False, blank=False)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='propietario')
    login_username = models.CharField('Nombre de usuario', max_length=50, null=False, blank=False, default="kodi")
    login_password = models.CharField('Contraseña', max_length=50, null=True, blank=True)

    def get_json_rpc_url(self):
        host_url = self.host_url

        if self.login_username and self.login_password:
            protocol_part = "http://"
            if host_url.startswith("https://"):
                protocol_part = "https://"

            host_url = host_url.replace(protocol_part, "%s%s:%s" % (
                protocol_part, self.login_username, self.login_password
            ))

        return '%s/jsonrpc' % host_url