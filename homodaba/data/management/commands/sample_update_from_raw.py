from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.utils.translation import gettext as _
from django.utils.text import slugify


from data.models import Movie, ContentRatingTag
from data.models import get_first_or_create_tag

import xml.etree.ElementTree as ET

"""
>>> from data.models import Movie
>>> zombieland = Movie.objects.filter(title='Zombieland')[0]
>>> xml_movie = ET.fromstring(zombieland.imdb_raw_data)
>>> xml_movie.findall("//certificates/item")

"""

class Command(BaseCommand):
    help = _('Ejemplo de modificacion de datos masiva usando el xml en imdb_raw_data')

    def handle(self, *args, **options):
        """
        Para este ejemplo lo que vamos a hacer es actualizar el content_rating_systems... 
        que se me olvido en el import_csv :P
        """
        for movie in Movie.objects.all():
            # Si ya tiene content_rating_systems pasamos de el
            if movie.content_rating_systems.count() == 0:
                """
                Si no tenemos:
                * Cargamos los datos xml
                * Buscamos elementos <certificates><item /></certificates>
                * Para cada uno de esos elementos si tiene alguno 
                    que empieze por 'United States:'
                * Quitamos el 'United States:' y comparamos por si lo hubieramos
                    insertado ya...
                """
                xml = ET.fromstring(movie.imdb_raw_data)
                certs = xml.findall("certificates/item")
                valid_certs = []
                if len(certs) > 0:
                    for c in certs:
                        if c.text.startswith('United States:'):
                            valid_cert = c.text.replace('United States:', '')
                            if not valid_cert in valid_certs:
                                valid_certs.append(valid_cert)
                
                if len(valid_certs) == 0:
                    print('INFO: No se encontraron clasificaciones de edad para "%s"' % movie.get_complete_title())
                else:
                    for vc in valid_certs:
                        movie.content_rating_systems.add(
                            get_first_or_create_tag(
                                ContentRatingTag, name=vc
                            )
                        )
                    movie.save()
