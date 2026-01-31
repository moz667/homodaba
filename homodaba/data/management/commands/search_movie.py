from django.core.management.base import BaseCommand

from data.models import Person

from data.utils import Trace as trace
from data.utils.imdbpy_facade import facade_search, match_director, clean_string

import csv
from distutils.util import strtobool

from .utils import clean_csv_data
from .import_csv import HELP_TEXT # Utiliza el mismo archivo csv que import_csv.py


# TODO: Buscar diferencias en year y director?

class Command(BaseCommand):
    help = 'Localiza cambios entre el csv e imdb y los saca como un archivo json.'

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
        parser.add_argument('--title', nargs='+', type=str, help="""Titulo a buscar.""")
        parser.add_argument('--year', nargs='+', type=str, help="""Año a buscar.""")

    def get_csv_imdb_json_data(self, r, force_check_imdb_id=True):
        trace.debug('Tratando "%s (%s)"...' % (r['title'], r['year']))
        
        cd = clean_csv_data(r)

        not_an_imdb_movie = False
        if 'not_an_imdb_movie' in cd:
            if isinstance(cd['not_an_imdb_movie'], str) and cd['not_an_imdb_movie']:
                not_an_imdb_movie = strtobool(cd['not_an_imdb_movie'])
            elif cd['not_an_imdb_movie']:
                not_an_imdb_movie = True


        facade_result = facade_search(
            title=cd['title'], year=r['year'], 
            # title_alt=cd['title_alt'],
            # director=cd['director'],
            # storage_type=cd['storage_type'],
            # storage_name=cd['storage_name'],
            # path=cd['path'],
            # imdb_id=cd['imdb_id'],
            # not_an_imdb_movie=not_an_imdb_movie
        )

        if not facade_result:
            trace.error('Parece que no encontramos la pelicula "%s (%s)"' % (cd['title'], r['year']))
            return None

        # Si ya hemos puesto el imdb_id no tiene sentido comprobar, la damos 
        # por bueba
        if not force_check_imdb_id and cd['imdb_id']:
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

        directors = []

        if facade_result.is_local_data:
            json_obj['db_info']['title'] = m.title
            json_obj['db_info']['imdb_id'] = m.imdb_id
            json_obj['db_info']['db_id'] = m.id
            json_obj['db_info']['year'] = m.year

            for d in m.get_directors():
                directors.append({
                    'db_id': d.id,
                    'name': d.name,
                    'canonical_name': d.canonical_name,
                    'imdb_id': d.imdb_id,
                })
        else:
            trace.warning('La pelicula "%s (%s)" no se encuentra en la base de datos.' % (r['title'], r['year']))

            json_obj['db_info']['title'] = m['title']
            json_obj['db_info']['imdb_id'] = m.getID()
            json_obj['db_info']['db_id'] = None
            json_obj['db_info']['year'] = int(m['year'])

            if 'director' in m.keys():
                for imdb_director in m['director']:
                    local_db_directors = Person.objects.filter(imdb_id=imdb_director.getID()).all()
                    local_db_director = local_db_directors[0] if local_db_directors.count() > 0 else None

                    if local_db_director is None:
                        directors.append({
                            'db_id': None,
                            'name': imdb_director['name'],
                            'canonical_name': imdb_director['canonical_name'],
                            'imdb_id': imdb_director.getID(),
                        })
                    else:
                        directors.append({
                            'db_id': local_db_director.id,
                            'name': local_db_director.name,
                            'canonical_name': local_db_director.canonical_name,
                            'imdb_id': local_db_director.imdb_id,
                        })

        json_obj['db_info']['directors'] = directors

        has_error = False

        if clean_string(json_obj['db_info']['title']) != clean_string(cd['title']):
            trace.warning(" - No coincide el titulo csv:'%s' db:'%s'." % (cd['title'], json_obj['db_info']['title']))
            has_error = True

        if not cd['year']:
            trace.warning(" - No esta definido el año en el csv para la pelicula '%s'." % cd['title'])
            has_error = True

        if json_obj['db_info']['year'] != int(cd['year']):
            trace.warning(" - No coincide el año en la pelicula '%s'. csv:'%s' db:'%s'." % (cd['title'], cd['year'], json_obj['db_info']['year']))
            has_error = True

        has_director_error = False
        if 'director' in cd and cd['director']:
            if not match_director(cd['director'], json_obj['db_info']['directors']):
                trace.warning(" - No hemos encontrado el/los director/es '%s' para la pelicula '%s'." % (cd['director'], cd['title']))
                has_error = True
                has_director_error = True

        if has_director_error:
            trace.warning(" - Los directores de la pelicula '%s' son:" % cd['title'])
            for cur_director in json_obj['db_info']['directors']:
                trace.warning("\t * '%s'." % cur_director['name'])

        return json_obj if has_error else None


    def handle(self, *args, **options):
        if not 'title' in options or not options['title'] or not options['title'][0]:
            self.print_help('manage.py', __name__)
            return

        if not 'year' in options or not options['year'] or not options['year'][0]:
            self.print_help('manage.py', __name__)
            return

        query = {}
        query['title'] = options['title'][0]
        query['year'] = options['year'][0]

        cur_movie = self.get_csv_imdb_json_data(query, True)

        print(cur_movie)


