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

    def search_and_print(self, r, force_check_imdb_id=True):
        trace.debug('Tratando "%s (%s)"...' % (r['title'], r['year']))
        
        cd = clean_csv_data(r)
        
        facade_result = facade_search(
            title=cd['title'], year=r['year'], exclude_local_data=True
        )

        if facade_result is None or facade_result.movie is None:
            print('No encontramos la pelicula')
            return

        m = facade_result.movie

        print('## %s (%s) imdb_id="%s" tmdb_id="%s"' % (m.title, m.year, m.imdb_id, m.tmdb_id))

        print('')
        print(m.summary)
        print('')

        print('* title="%s"' % m.title)
        print('* title_original="%s"' % m.title_original)
        print('* title_preferred="%s"' % m.title_preferred)
        print('* kind="%s"' % m.kind)
        
        print('* poster_url="%s"' % m.poster_url)
        print('* poster_thumbnail_url="%s"' % m.poster_thumbnail_url)
        print('* rating="%s"' % m.rating)

        print ('* Title AKAS:')
        if len(m.title_akas) > 0:
            for country in m.title_akas.keys():
                print('    - %s (%s)' % (m.title_akas[country], country))
        else:
            print ('    - No tiene title AKAS')

        print ('* Tags:')
        if len(m.tags) > 0:
            for t in m.tags:
                print('    - %s' % t)
        else:
            print ('    - No tiene tags')

        print ('* Genres:')
        if len(m.genres) > 0:
            for t in m.genres:
                print('    - %s' % t)
        else:
            print ('    - No tiene genres')

        print ('* Content rating systems:')
        if len(m.content_rating_systems) > 0:
            for t in m.content_rating_systems:
                print('    - %s' % t)
        else:
            print ('    - No tiene content rating systems')

        print ('* Directores:')
        if len(m.directors) > 0:
            for fc in m.directors:
                print('    - %s (%s)' % (fc.name, fc.avatar_url if not fc.avatar_url is None else 'No tiene avatar'))
        else:
            print ('    - No tiene directores')

        print ('* Escritores:')
        if len(m.writers) > 0:
            for fc in m.writers:
                print('    - %s (%s)' % (fc.name, fc.avatar_url if not fc.avatar_url is None else 'No tiene avatar'))
        else:
            print ('    - No tiene escritores')

        print ('* Actores:')
        if len(m.actors) > 0:
            for fc in m.actors:
                print('    - %s (%s)' % (fc.name, fc.avatar_url if not fc.avatar_url is None else 'No tiene avatar'))
        else:
            print ('    - No tiene actores')


        print ('* Paises:')
        if len(m.countries) > 0:
            for t in m.countries:
                print('    - %s' % t)
        else:
            print ('    - No tiene paises')





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

        self.search_and_print(query, True)


