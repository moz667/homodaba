from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.utils.translation import gettext as _
from django.utils.text import slugify

from data.models import Movie, Person, MovieStorageType, MoviePerson, Tag, GenreTag, TitleAka, ContentRatingTag
from data.models import get_first_or_create_tag

from data.utils.imdbpy_facade import facade_search

import csv
from datetime import datetime
import sys

from .utils import trace_validate_imdb_movie, get_imdb_original_title, normalize_age_certificate

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
        parser.add_argument('--from-title', nargs='+', type=str, help="""Empieza a tratar desde la fila que se titule igual que el valor de este parametro.""")
        parser.add_argument('--imdba-delay', nargs='+', type=int, help="""Retardo entre llamadas al imdb (util si te da muchos errores de conexion).""")
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
    
    def clean_path_no_extension_and_title(self, title):
        clean_title = title
        if '/' in clean_title:
            clean_title = title.split('/')[-1]
        if '.' in clean_title:
            clean_title = title.split('.')[-1]

        return clean_title.strip()

    def check_movie(self, r):
        # print('Tratando "%s (%s)"...' % (r['title'], r['year']))
        
        title = r['title']
        title_alt = r['title_preferred'] if 'title_preferred' in r and r['title_preferred'] else None
        storage_name = r['storage_name'] if 'storage_name' in r and r['storage_name'] and r['storage_name'] != 'Original' else None
        director = r['director'] if 'director' in r and r['director'] else None
        is_original = True if not storage_name else False
        imdb_id = r['imdb_id'] if 'imdb_id' in r and r['imdb_id'] else None

        storage_type = MovieStorageType.ST_DVD
        if 'storage_type' in r and r['storage_type']:
            if not r['storage_type'] in MovieStorageType.STORAGE_TYPES_AS_LIST:
                print('\tWARNING! storage_type "%s" no encontrado en la lista de soportados.' % r['storage_type'])
            else:
                storage_type = r['storage_type']
        
        media_format = MovieStorageType.MF_DVD
        if 'media_format' in r and r['media_format']:
            if not r['media_format'] in MovieStorageType.MEDIA_FORMATS_AS_LIST:
                print('\tWARNING! media_format "%s" no encontrado en la lista de soportados.' % r['media_format'])
            else:
                media_format = r['media_format']

        path = r['path'] if not is_original and 'path' in r and r['path'] else None

        if not is_original and not path and 'path_no_extension' in r and r['path_no_extension']:
            path = r['path_no_extension']
            if media_format:
                if media_format in MovieStorageType.MEDIA_FORMATS_FILE_WITH_ISO_EXTENSION:
                    path = path + ".iso"
                elif media_format in MovieStorageType.MEDIA_FORMATS_FILE_WITH_OTHER_EXTENSION:
                    path = path + ".%s" % media_format.lower()

        version = r['version'] if 'version' in r and r['version'] else None
        resolution = r['resolution'] if 'resolution' in r and r['resolution'] else None

        # TODO: chequear !!!

        # Las originales no podemos chequearlas
        if is_original:
            return
        
        # print(title)
        mmsstt = MovieStorageType.objects.filter(
            is_original=is_original, 
            storage_type=storage_type, 
            name=storage_name,
            path=path,
            media_format=media_format,
            resolution=resolution,
            version=version,
        ).all()

        if mmsstt.count() == 0:
            print("\tERROR: No encontramos el mst para la pelicula '%s'" % title)
        elif mmsstt.count() > 1:
            print("\tERROR: Hemos encontramos varios mst para la pelicula '%s'" % title)
        else:
            if int(r['year']) != int(mmsstt[0].movie.year):
                print("\tERROR: La pelicula '%s' es de un año distinto (%s) vs (%s) en la bbdd." % (title, r['year'], mmsstt[0].movie.year))
            if title != mmsstt[0].movie.title:
                print("\tERROR: La pelicula '%s' tiene un titulo distinto (%s) en la bbdd." % (title,  mmsstt[0].movie.title))

    def handle(self, *args, **options):
        if options['csv_file_help']:
            self.csv_file_help()
        
        if not 'csv_file' in options or not options['csv_file'] or not options['csv_file'][0]:
            self.print_help('manage.py', __name__)
            return

        csv_delimiter = ';'
        if 'delimiter' in options and options['delimiter'] and options['delimiter'][0]:
            csv_delimiter = options['delimiter'][0]

        csv_quotechar = '|'
        if 'quotechar' in options and options['quotechar'] and options['quotechar'][0]:
            csv_quotechar = options['quotechar'][0]

        from_title = options['from_title'] if 'from_title' in options and options['from_title'] and len(options['from_title']) > 0 else None
        from_title = ' '.join(from_title) if from_title else None

        global verbosity
        verbosity = options['verbosity']
        fieldnames = []

        with open(options['csv_file'][0], newline='') as csvfile:
            csv_reader = csv.DictReader(csvfile, delimiter=csv_delimiter, quotechar=csv_quotechar)
            fieldnames = csv_reader.fieldnames
            for r in csv_reader:
                self.validate(r)
        
        now = datetime.now()

        with open(options['csv_file'][0], newline='') as csvfile:
            csv_reader = csv.DictReader(csvfile, delimiter=csv_delimiter, quotechar=csv_quotechar)
            
            start = not from_title

            for csv_row in csv_reader:
                if from_title and from_title == csv_row['title']:
                    start = True
                
                if start:
                    try:
                        self.check_movie(csv_row)
                    except:
                        print("Error no esperado:", sys.exc_info()[0])
                        raise
