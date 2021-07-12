from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.utils.translation import gettext as _
from django.utils.text import slugify

from data.models import Movie, Person, MovieStorageType, MoviePerson, Tag, GenreTag, TitleAka, ContentRatingTag
from data.models import get_first_or_create_tag

from data.utils.imdbpy_facade import facade_search

import csv
import sys

verbosity = 0

HELP_TEXT = """
Descripcion de los campos del csv:

OBLIGATORIOS:
    title: Titulo de la pelicula (OBLIGATORIO)

    year: Año de estreno (OBLIGATORIO)

OPCIONALES:
    imdb_id: Identificador de imdb para forzar la busqueda de esa peli (por defecto: 
        None) (opcional)

    storage_name: identificador del almacenamiento (nombre del disco duro, 
        carpeta compartida...) (opcional, aunque hay que tener en cuenta
        que si no se define, ó es 'Original', tomara que el medio es 
        original)

    media_format: Formato en el que esta almacenado el medio (ver 
        models.MovieStorageType.MEDIA_FORMATS para mas info de los 
        disponibles) (opcional, por defecto DVD)

    storage_type: Tipo de almacenamiento en el se encuentra el medio 
        (ver models.MovieStorageType.STORAGE_TYPES para mas info de los 
        disponibles) (opcional, por defecto DVD)

    path_no_extension: Campo especial para definir donde se almacena el 
        medio SIN EXTENSION de archivo (en caso de discos duros, carpetas 
        compartidas...) (opcional)

    path: Ruta completa (con extension si fuera necesaria) al medio
        (opcional, hay que tener en cuenta que si path no tiene valor, pero
        por el contrario hemos incluido el campo path_no_extension, 
        intentara averiguar el valor de path en base a path_no_extension y
        media_format, por ejemplo para estos valores:
        media_format=AVI
        path_no_extension=carpeta/fichero_sin_extension
        path se calculara como:
        path=carpeta/fichero_sin_extension.avi)

    title_preferred: Titulo en el idioma materno del usuario (por defecto: 
        Español) (opcional)

    director: Director de la pelicula (directores separados por coma) 
        (opcional y no muy necesario ya que esa info nos la da 
        alegremente imdb)

    resolution: Resolución del medio (1080p, 2060p... etc) (opcional)
    
    tags: Etiquetas separadas por coma, lo usamos para identificar sagas (optional)
    
    title_original: Titulo original de la película, si se suministra ignora
        el de imdb que parece que siempre lo devuelve en ingles.

    version: Version de la película, (Director's cut, Theatrical's cut...) (opcional)
"""

class Command(BaseCommand):
    help = _('Importa datos desde un CSV')

    """
    Pinta la ayuda y sale
    """
    def csv_file_help(self):
        print(HELP_TEXT)
        exit()

    """
    Valida los datos de una fila del csv, si hay algun error lanza Exception

    Ahora mismo solo valida que tenga titulo (title) y año (year)
    """
    def validate(self, r):
        if not 'title' in r or not r['title']:
            raise Exception("ERROR!: El titulo es obligatorio y tiene que estar definido en el CSV como 'title'.")
        if not 'year' in r or not r['year']:
            raise Exception("ERROR!: El año de estreno es obligatorio y tiene que estar definido en el CSV como 'year'.")

    """
    Argumentos del comando:

    """
    def add_arguments(self, parser):
        parser.add_argument('--csv-file', nargs='+', type=str, help="""Fichero csv con los datos a importar.""")
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
    
    def check_movie(self, mst, csv_file, csv_newline='', csv_delimiter=';', csv_quotechar='|'):
        # print('Tratando "%s (%s)"...' % (r['title'], r['year']))
        with open(csv_file, newline=csv_newline) as csvfile:
            csv_reader = csv.DictReader(csvfile, delimiter=csv_delimiter, quotechar=csv_quotechar)

            for r in csv_reader:
                if r['path'] == mst.path and r['title'] == mst.movie.title:
                    # print("\tOK: La pelicula '%s' tiene el mismo titulo (%s) que en la bbdd." % (r['title'],  mst.movie.title))
                    return
            
            print("\tERROR: Posible coincidencia de duplicados '%s'" % (mst.movie.title))
            
            mmsstt = MovieStorageType.objects.filter(
                movie=mst.movie
            ).all()
            for m in mmsstt:
                print('\t\t(%s)%s' % (m.storage_type, m.path))
    
    def handle(self, *args, **options):
        if options['csv_file_help']:
            self.csv_file_help()
        
        if not 'csv_file' in options or not options['csv_file'] or not options['csv_file'][0]:
            self.print_help('manage.py', __name__)
            return
        csv_file = options['csv_file'][0]

        csv_delimiter = ';'
        if 'delimiter' in options and options['delimiter'] and options['delimiter'][0]:
            csv_delimiter = options['delimiter'][0]

        csv_quotechar = '|'
        if 'quotechar' in options and options['quotechar'] and options['quotechar'][0]:
            csv_quotechar = options['quotechar'][0]

        global verbosity
        verbosity = options['verbosity']
        fieldnames = []

        with open(options['csv_file'][0], newline='') as csvfile:
            csv_reader = csv.DictReader(csvfile, delimiter=csv_delimiter, quotechar=csv_quotechar)
            fieldnames = csv_reader.fieldnames
            for r in csv_reader:
                self.validate(r)
        
        for movie in Movie.objects.all():
            mmsstt = MovieStorageType.objects.filter(
                movie=movie
            ).all()

            if mmsstt.count() == 0:
                print("\tERROR: No encontramos el mst para la pelicula '%s'" % movie.title)
            elif mmsstt.count() > 1:
                # print("\tERROR: Hemos encontramos varios mst para la pelicula '%s'" % movie.title)

                for mst in mmsstt:
                    if not mst.is_original:
                        self.check_movie(mst, csv_file, csv_delimiter=csv_delimiter, csv_quotechar=csv_quotechar)