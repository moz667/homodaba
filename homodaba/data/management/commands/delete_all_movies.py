from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import gettext as _

from data.models import Movie, TitleAka, ContentRatingTag, Person, Tag, GenreTag, UserTag
from data.utils import Trace as trace

from django.db import connection
from django.db import connections

from homodaba.settings import DATABASES

import csv
import getch

HELP_TEXT = """
Descripcion de los campos del csv:

OBLIGATORIOS:
    title: Titulo de la pelicula en la base de datos
"""

class Command(BaseCommand):
    help = _("""Borra los datos de peliculas""")

    """
    Pinta la ayuda y sale
    """
    def csv_file_help(self):
        print(HELP_TEXT)
        exit()

    def add_arguments(self, parser):
        parser.add_argument('--csv-file', nargs='+', type=str, help="""Fichero csv con los titulos a borrar.""")
        parser.add_argument(
            '--csv-file-help',
            action='store_true',
            help='Ayuda ampliada acerca del archivo csv.',
        )
        parser.add_argument(
            '--delimiter', default=';',
            type=str,
            help='Delimitador de campos para el csv (por defecto ";")',
        )
        parser.add_argument(
            '--quotechar', default='|',
            type=str,
            help='Caracter de encomillado para cadenas del csv (por defecto "|")',
        )
        parser.add_argument(
            '--delete-all-data',
            action='store_true',
            help='Borra todo menos la cache...',
        )
        parser.add_argument(
            '--cache-database',
            action='store_true',
            help='Borra los datos de la base de datos de cache (en vez de la base de datos por defecto).',
        )


    def handle(self, *args, **options):
        csv_file = None
        csv_delimiter = ';'
        csv_quotechar = '|'

        delete_all_data = options['delete_all_data']
        delete_from_cache = options['cache_database']
        database = 'default'

        if delete_from_cache and 'cache' in DATABASES.keys():
            database = 'cache'
        
        print("")
        print(" * Esta seguro que desea borrar los datos de peliculas de la base de datos '%s' ? [y/N]: " % database)

        selected_option = getch.getch()

        if selected_option.lower() == 'y':
            if 'csv_file' in options and options['csv_file'] and len(options['csv_file']) > 0:
                csv_file = ' '.join(options['csv_file'])

                if 'delimiter' in options and options['delimiter'] and options['delimiter'][0]:
                    csv_delimiter = options['delimiter'][0]

                if 'quotechar' in options and options['quotechar'] and options['quotechar'][0]:
                    csv_quotechar = options['quotechar'][0]

                with open(csv_file, newline='') as csvfile:
                    csv_reader = csv.DictReader(csvfile, delimiter=csv_delimiter, quotechar=csv_quotechar)

                    for csv_row in csv_reader:
                        if 'title' in csv_row:
                            Movie.objects.using(database).filter(title=csv_row['title']).delete()
            else:
                Movie.objects.using(database).all().delete()

            if delete_all_data:
                if len(Movie.objects.all()) > 0:
                    trace.error("No podemos borrar todos los datos ya que aun existe peliculas.")
                else:
                    TitleAka.objects.using(database).all().delete()
                    ContentRatingTag.objects.using(database).all().delete()
                    Person.objects.using(database).all().delete()
                    Tag.objects.using(database).all().delete()
                    GenreTag.objects.using(database).all().delete()
                    UserTag.objects.using(database).all().delete()
                    """
                    FIXME: Hay un problema con las tablas intermedias que no permite grabar
                    with connections[database].cursor() as cursor:
                        cursor.execute('TRUNCATE TABLE {0}'.format(TitleAka._meta.db_table))
                        cursor.execute('TRUNCATE TABLE {0}'.format(ContentRatingTag._meta.db_table))
                        cursor.execute('TRUNCATE TABLE {0}'.format(Person._meta.db_table))
                        cursor.execute('TRUNCATE TABLE {0}'.format(Tag._meta.db_table))
                        cursor.execute('TRUNCATE TABLE {0}'.format(GenreTag._meta.db_table))
                        cursor.execute('TRUNCATE TABLE {0}'.format(UserTag._meta.db_table))
                        cursor.execute('TRUNCATE TABLE {0}'.format(Movie._meta.db_table))
                    """
            
            print("")
            print(" # Datos borrados #")
            print("")