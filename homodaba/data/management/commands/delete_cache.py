from django.core.management.base import BaseCommand
from django.utils.translation import gettext as _

from data.models import ImdbCache, get_imdb_cache_objects

from homodaba.settings import DATABASES

import getch

class Command(BaseCommand):
    help = _("""Borra los datos de cache""")
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--default-database',
            action='store_true',
            help='Borra los datos de la base de datos por defecto (en vez de la base de datos de cache).',
        )

    def handle(self, *args, **options):
        delete_from_default = options['default_database']

        objects = get_imdb_cache_objects()
        database = 'cache' if 'cache' in DATABASES.keys() else 'default'

        if delete_from_default:
            objects = ImdbCache.objects.using('default')
            database = 'default'

        print("")
        print(" * Esta seguro que desea borrar toda la cache de la base de datos '%s' ? [y/N]: " % database)
        
        selected_option = getch.getch()

        if selected_option.lower() == 'y':
            objects.all().delete()

            print("")
            print(" # Cache borrada #")
            print("")