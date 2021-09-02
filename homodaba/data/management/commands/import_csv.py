from django.core.management.base import BaseCommand

from data.models import Tag
from data.models import get_first_or_create_tag, populate_movie_auto_tags

from data.utils import Trace as trace
from data.utils.imdbpy_facade import facade_search, get_imdb_titles

import csv
from datetime import datetime
import sys

from .utils import trace_validate_imdb_movie, clean_csv_data, csv_validate

from .import_data import get_or_insert_storage, insert_movie_from_imdb, insert_movie_from_a_not_an_imdb_movie, populate_local_movie_tags

HELP_TEXT = """
Descripcion de los campos del csv:

OBLIGATORIOS:
    title: Titulo de la pelicula (OBLIGATORIO)

    year: Año de estreno (OBLIGATORIO)

OPCIONALES:
    imdb_id: Identificador de imdb para forzar la busqueda de esa peli (por defecto: 
        None) (opcional)

    not_an_imdb_movie: Indica que es una pelicula que no se encuentra en imdb. 
        Esto es util para que el procesador no busque esas peliculas en el imdb
        y nos de la murga con errores :P

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
    help = 'Importa datos desde un CSV'

    """
    Pinta la ayuda y sale
    """
    def csv_file_help(self):
        print(HELP_TEXT)
        exit()

    """
    Argumentos del comando:

    """
    def add_arguments(self, parser):
        parser.add_argument('--csv-file', nargs='+', type=str, help="""Fichero csv con los datos a importar.""")
        parser.add_argument('--from-title', nargs='+', type=str, help="""Empieza a tratar desde la fila que se titule igual que el valor de este parametro.""")
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

    def process_movie(self, r):
        trace.info('Tratando "%s (%s)"...' % (r['title'], r['year']))
        
        cd = clean_csv_data(r)

        not_an_imdb_movie = cd['not_an_imdb_movie']

        facade_result = facade_search(
            title=cd['title'], year=r['year'], 
            title_alt=cd['title_alt'],
            director=cd['director'],
            storage_type=cd['storage_type'],
            storage_name=cd['storage_name'],
            path=cd['path'],
            imdb_id=cd['imdb_id'],
            not_an_imdb_movie=not_an_imdb_movie
        )

        tags = cd['tags']

        if not facade_result and not not_an_imdb_movie:
            trace.error('\tParece que no encontramos la pelicula "%s (%s)"' % (cd['title'], r['year']))
            return None

        local_movie = None

        # Para las que no encuentra pero que se tratan de pelis que no son 
        # localizables en el imdb, las insertamos con los datos que tenemos
        if not facade_result and not_an_imdb_movie:
            local_movie = insert_movie_from_a_not_an_imdb_movie(
                title=cd['title'], 
                year=cd['year'], 
                directors=cd['directors'], 
                tags=tags, 
                title_original=cd['title_original'], 
                title_preferred=cd['title_preferred'], 
            )
        # Para pelis que ya hemos insertado anteriormente
        elif facade_result.is_local_data:
            # 1.1) si la esta, sacamos un mensaje y devolvemos la pelicula (FIN)
            trace.warning("\tYa tenemos una película con el título '%s' del año '%s'" % (cd['title'], r['year']))

            local_movie = facade_result.movie
        # El resto son pelis nuevas (localizables por el imdb)
        else:
            trace_validate_imdb_movie(facade_result.movie, cd['title'], director=cd['director'])

            local_movie = insert_movie_from_imdb(
                r['title'],
                facade_result.movie, 
                tags=tags, 
                title_original=cd['title_original'],
                title_preferred=cd['title_preferred'],
            )

        # Solo insertamos storage si no fue una coincidencia de storage o se 
        # trata de una peli nueva
        if not facade_result or not facade_result.storage_match:
            get_or_insert_storage(
                movie=local_movie, 
                is_original=cd['is_original'], 
                storage_type=cd['storage_type'], 
                storage_name=cd['storage_name'], 
                path=cd['path'], 
                resolution=cd['resolution'], 
                media_format=cd['media_format'], 
                version=cd['version'], 
            )

        # Puede ocurrir, cuando se trata de un nuevo storage, que lleve nuevas 
        # tags (por ejemplo, una version extendida de una peli, 3D...)
        # es por esto que siempre comprobamos tags aunque la peli ya haya
        # sido dada de alta con anterioridad
        populate_local_movie_tags(local_movie, tags)

        return local_movie

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

        verbosity = options['verbosity']
        trace.set_verbosity(verbosity)

        fieldnames = []

        with open(options['csv_file'][0], newline='') as csvfile:
            csv_reader = csv.DictReader(csvfile, delimiter=csv_delimiter, quotechar=csv_quotechar)
            fieldnames = csv_reader.fieldnames
            for r in csv_reader:
                csv_validate(r)
        
        now = datetime.now()

        csv_fails = open('fail-%s.csv' % now.strftime('%Y%m%d-%H%M%S'), 'w', newline='')
        csv_done = open('done-%s.csv' % now.strftime('%Y%m%d-%H%M%S'), 'w', newline='')
        csv_writer_fails = csv.DictWriter(csv_fails, fieldnames=fieldnames, delimiter=csv_delimiter, quotechar=csv_quotechar)
        csv_writer_done = csv.DictWriter(csv_done, fieldnames=fieldnames, delimiter=csv_delimiter, quotechar=csv_quotechar)
        csv_writer_fails.writeheader()
        csv_writer_done.writeheader()

        with open(options['csv_file'][0], newline='') as csvfile:
            csv_reader = csv.DictReader(csvfile, delimiter=csv_delimiter, quotechar=csv_quotechar)
            
            start = not from_title

            for csv_row in csv_reader:
                if from_title and from_title == csv_row['title']:
                    start = True
                
                if start:
                    try:
                        cur_movie = self.process_movie(csv_row)
                        if cur_movie is None:
                            csv_writer_fails.writerow(csv_row)
                        else:
                            csv_writer_done.writerow(csv_row)
                    except:
                        trace.error("Error no esperado", sys.exc_info()[0])
                        csv_writer_fails.writerow(csv_row)
                        raise

                    trace.debug("")
