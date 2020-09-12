from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.utils.translation import gettext as _
from django.utils.text import slugify


from data.models import Movie, TitleAka
from data.models import get_first_or_create_tag

import re
import xml.etree.ElementTree as ET

"""
>>> from data.models import Movie
>>> zombieland = Movie.objects.filter(title='Zombieland')[0]
>>> xml_movie = ET.fromstring(zombieland.imdb_raw_data)
>>> xml_movie.findall("//certificates/item")

"""

class Command(BaseCommand):
    help = _("""Esto es un cambio que veo necesario para poder hacer mejores 
busquedas a traves de los akas. originalmente guardaba todo lo que venia de imdb
pero no tiene mucho sentido, vamos a quitar la parte que especifica el contexto 
del aka (una parte que va entre parentesis) para que solo 
alamacene el titulo en si.

Antes de ejecutar conviene borrar la tabla primero con el argumento:
'--clear-akas'""")

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear-akas',
            action='store_true',
            help='Borra la tabla de akas al principio.',
        )

    def handle(self, *args, **options):
        """
        Esto es un cambio que veo necesario para poder hacer mejores busquedas
        a traves de los akas. originalmente guardaba todo lo que venia de imdb
        pero no tiene mucho sentido, vamos a quitar la parte que especifica el
        contexto del aka (una parte que va entre parentesis) para que solo 
        alamacene el titulo en si.

        Antes de ejecutar conviene borrar la tabla primero:
        --clear-akas
        TitleAka.objects.all().delete()
        """
        if 'clear_akas' in options and options['clear_akas']:
            TitleAka.objects.all().delete()
        
        for movie in Movie.objects.all():
            xml = ET.fromstring(movie.imdb_raw_data)
            aka_elements = xml.findall("akas/item")
            valid_akas = []
            if len(aka_elements) > 0:
                for aka_el in aka_elements:
                    clean_aka = re.compile(' \(.*').sub('', aka_el.text)
                    if not clean_aka in valid_akas:
                        valid_akas.append(clean_aka)

            if len(valid_akas) == 0:
                print('INFO: No se encontraron akas para "%s"' % movie.get_complete_title())
            else:
                for aka in valid_akas:
                    movie.title_akas.add(
                        get_first_or_create_tag(
                            TitleAka, title=aka
                        )
                    )
                movie.save()
