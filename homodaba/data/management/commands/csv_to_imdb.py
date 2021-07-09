from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.utils.translation import gettext as _
from django.utils.text import slugify

from data.models import Movie, Person, MovieStorageType, MoviePerson, Tag, GenreTag, TitleAka, ContentRatingTag
from data.models import get_first_or_create_tag

from data.utils.imdbpy_facade import facade_search

import csv
from datetime import datetime
import json
import sys

from .utils import trace_validate_imdb_movie, get_imdb_original_title, normalize_age_certificate, clean_csv_data, csv_validate
from .import_csv import HELP_TEXT # Utiliza el mismo archivo csv que import_csv.py


verbosity = 0

# TODO: Buscar diferencias en year y director?

class Command(BaseCommand):
    help = _('Localiza cambios entre el csv e imdb y los saca como un archivo json.')

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
        parser.add_argument('--csv-file', nargs='+', type=str, help="""Fichero csv con los datos a comprobar.""")
        parser.add_argument('--from-title', nargs='+', type=str, help="""Empieza a comprobar desde la fila que se titule igual que el valor de este parametro.""")
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


    def get_or_create_person(self, ia_person):
        local_persons = Person.objects.filter(imdb_id=ia_person.getID()).all()

        if local_persons.count() > 0:
            return local_persons[0]
        
        return Person.objects.create(
            name=ia_person['name'],
            canonical_name=ia_person['canonical name'],
            imdb_id=ia_person.getID(),
        )

    def get_csv_imdb_json_data(self, r):
        # print('Tratando "%s (%s)"...' % (r['title'], r['year']))
        
        cd = clean_csv_data(r)

        facade_result = facade_search(
            title=cd['title'], year=r['year'], 
            title_alt=cd['title_alt'],
            director=cd['director'],
            storage_type=cd['storage_type'],
            storage_name=cd['storage_name'],
            path=cd['path'],
            imdb_id=cd['imdb_id'],
        )

        if not facade_result:
            print('\tERROR!: Parece que no encontramos la pelicula "%s (%s)"' % (cd['title'], r['year']))
            return None

        json_obj = {}
        json_obj['csv_info'] = {}
        json_obj['db_info'] = {}
        json_obj['csv_info'] = {
            'title': cd['title'],
            'title_preferred': cd['title_alt'],
            'year': cd['year'],
            'director': cd['director'],
        }
        m = facade_result.movie

        if facade_result.is_local_data:
            json_obj['db_info']['title'] = m.title
            json_obj['db_info']['imdb_id'] = m.imdb_id
            json_obj['db_info']['db_id'] = m.id
            json_obj['db_info']['year'] = m.year
        else:
            print('\tWARNING: La pelicula "%s (%s)" no se encuentra en la base de datos.' % (r['title'], r['year']))

            json_obj['db_info']['title'] = m['title']
            json_obj['db_info']['imdb_id'] = m.getID()
            json_obj['db_info']['db_id'] = None



        if json_obj['db_info']['title'] == cd['title']:
            return None

        return json_obj


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
                csv_validate(r)
        
        now = datetime.now()

        json_obj = []

        with open(options['csv_file'][0], newline='') as csvfile:
            csv_reader = csv.DictReader(csvfile, delimiter=csv_delimiter, quotechar=csv_quotechar)
            
            start = not from_title

            for csv_row in csv_reader:
                if from_title and from_title == csv_row['title']:
                    start = True
                
                if start:
                    try:
                        cur_movie = self.get_csv_imdb_json_data(csv_row)
                        if not cur_movie is None:
                            json_obj.append(cur_movie)
                    except:
                        print("ERROR en '%s'" % csv_row['title'])
                        print("Error no esperado:", sys.exc_info()[0])
                        raise
        
        print("")

        if len(json_obj) == 0:
            print(" * CONGRATZ!!!")

            print("   - No hay ninguna pelicula en el csv con titulo distinto al imdb.")
        else:
            now = datetime.now()
            dump_filename = 'csv2imdb-%s.json' % now.strftime('%Y%m%d-%H%M%S')
            dump_file = open(dump_filename, 'w', newline='')
            dump_file.write(json.dumps(json_obj, indent=4, sort_keys=True, ensure_ascii=False))

            print(" * WARNING!!!")

            print("   - Se han encontrado %s en el csv con titulo distinto al imdb." % 
                ('1 pelicula' if len(json_obj) == 1 else '%s peliculas' % len(json_obj))
            )

            print("   - Revisa el archivo '%s'." % 
                dump_filename
            )

