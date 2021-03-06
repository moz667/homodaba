from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import gettext as _

from data.models import Movie

import csv

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

    def handle(self, *args, **options):
        csv_file = None
        csv_delimiter = ';'
        csv_quotechar = '|'

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
                        Movie.objects.filter(title=csv_row['title']).delete()
        else:
             Movie.objects.all().delete()
