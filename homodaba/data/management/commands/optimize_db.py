from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.utils.translation import gettext as _
from django.utils.text import slugify


from data.models import Movie, TitleAka, MoviePerson, Tag
from data.models import get_first_or_create_tag, get_or_create_country, populate_movie_auto_tags

from data.utils import trace
from data.utils.imdbpy_facade import get_imdb_movie, get_imdb_titles

import csv
import re

HELP_TEXT = """
Este es un comando que hace muchas cosas:

1. Optimiza la base de datos y reduce el numero de relaciones de peliculas con 
otras entidades como TitleAka y MoviePerson a traves de las opciones:

    --clear-akas, Elimina todos los TitleAka

    --title-and-akas, Limpia los titulos principales y crea nuevos TitleAka 
    buscando solo las primeras coincidencias de:
        - Pais/es origen de la pelicula
        - Spanish
        - English

    (Antes de limpiar los aka conviene borrar la tabla primero.)

2. Completar la tabla intermedia de la lista de directores. Esto no deberia ser
necesario en versiones actuales de las importaciones (ya que se hace de forma 
automatica). Se hace con la opcion: --populate-directors

3. Actualizar la lista de tags de las peliculas a traves de un csv. El csv tiene 
que tener un campo que haga posible encontrar una pelicula (id de la bbdd ó imdb_id)
asi como un campo con las tags que queramos actualizar para el film separadas por 
comas. Las opciones que son necesarias aqui son:

    --csv-tag-file, fichero csv con la info de id y tags
    --delimiter, caracter para delimitar los campos en el csv (por defecto ";")
    --quotechar, Caracter de encomillado para cadenas del csv (por defecto "|")

4. Añade tags de forma automatica calculada en base a la  informacion de la 
pelicula. Por ahora solo creamos una tag con la decada del estreno del film, pero
seguro que se nos pueden ocurrir mas. Para poder hacer esto basta con pasarle 
la opcion "--create-auto-tags"

"""

class Command(BaseCommand):
    help = HELP_TEXT

    def add_arguments(self, parser):
        parser.add_argument(
            '--movie-id',
            type=str,
            help='Id de la pelicula sobre la que se realizaran las distintas funciones.',
        )
        parser.add_argument(
            '--clear-akas',
            action='store_true',
            help='Borra el contenido de la tabla de akas.',
        )
        parser.add_argument(
            '--title-and-akas',
            action='store_true',
            help='Optimiza y limpia los titulos principales y borra innecesarios TitleAka.',
        )
        parser.add_argument(
            '--populate-directors',
            action='store_true',
            help='Completa la lista de directores para cada pelicula.',
        )
        parser.add_argument(
            '--create-auto-tags',
            action='store_true',
            help='Añade tags de forma automatica calculada en base a la  informacion de la pelicula.',
        )
        parser.add_argument(
            '--csv-tag-file', 
            nargs='+', type=str, 
            help="""Fichero csv con id ó imdb_id y tags para actualizar."""
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
        verbosity = options['verbosity']
        trace.set_verbosity(verbosity)

        if 'clear_akas' in options and options['clear_akas']:
            TitleAka.objects.all().delete()
        
        query_movies = Movie.objects

        movie_id = int(options['movie_id']) if 'movie_id' in options and options['movie_id'] else None
        if movie_id:
            query_movies = Movie.objects.filter(id=movie_id)

        for movie in query_movies.all():
            trace.debug('>> %s (%s) [id:%s]' % (movie.title, movie.get_countries_as_text(), movie.id))
            if 'title_and_akas' in options and options['title_and_akas']:
                clean_title_and_akas(movie)
            if 'populate_directors' in options and options['populate_directors']:
                populate_directors(movie)
            if 'create_auto_tags' in options and options['create_auto_tags']:
                populate_movie_auto_tags(movie)
        
        if 'csv_tag_file' in options and options['csv_tag_file'] and options['csv_tag_file'][0]:
            csv_delimiter = ';'
            if 'delimiter' in options and options['delimiter'] and options['delimiter'][0]:
                csv_delimiter = options['delimiter'][0]

            csv_quotechar = '|'
            if 'quotechar' in options and options['quotechar'] and options['quotechar'][0]:
                csv_quotechar = options['quotechar'][0]

            with open(options['csv_tag_file'][0], newline='') as csvfile:
                csv_reader = csv.DictReader(csvfile, delimiter=csv_delimiter, quotechar=csv_quotechar)

                for csv_row in csv_reader:
                    tags = csv_row['tags'].split(",") if 'tags' in csv_row and csv_row['tags'] else []

                    if len(tags) > 0:
                        movies = None
                        if 'id' in csv_row and csv_row['id'] and (not movie_id or movie_id == int(csv_row['id'])):
                            movies = Movie.objects.filter(id=csv_row['id']).all()
                        elif 'imdb_id' in csv_row and csv_row['imdb_id']:
                            movies = Movie.objects.filter(imdb_id=csv_row['imdb_id']).all()
                        
                        if movies.count() > 0:
                            for movie in movies:
                                trace.debug('>> %s (%s) [id:%s]' % (movie.title, movie.get_countries_as_text(), movie.id))
                                tagged = False

                                for tag in tags:
                                    db_tag = get_first_or_create_tag(
                                        Tag, name=tag
                                    )

                                    if not db_tag in movie.tags.all():
                                        trace.debug(" * Añadiendo tag '%s'." % tag)
                                        tagged = True
                                        movie.tags.add(db_tag)
                                
                                if tagged:
                                    movie.save()

def populate_directors(movie):
    if movie.directors.count() > 0:
        trace.debug("  - Ya tenemos directores")
        return
    
    directors = MoviePerson.objects.filter(movie=movie, role=MoviePerson.RT_DIRECTOR).all()

    trace.debug("  - Añadimos los siguientes directores:")
    for director in directors:
        trace.debug("    * %s" % director.person.name)
        movie.directors.add(director.person)

    movie.save()

    

def clean_title_and_akas(movie):
    title_akas = {}
    new_titles = {}

    if movie.imdb_id:
        imdb_movie = get_imdb_movie(movie.imdb_id)

        # Completando paises de la peli
        if movie.countries.count() == 0 and 'countries' in imdb_movie.keys():
            for c in imdb_movie['countries']:
                movie.countries.add(get_or_create_country(
                    country=c
                ))
            movie.save()

        new_titles, title_akas = get_imdb_titles(imdb_movie)

        if len(title_akas.keys()) > 0:
            trace.debug(" * Los akas para la pelicula '%s' son:" % movie.title)

            movie.title_akas.clear()

            for country in title_akas.keys():
                trace.debug("    - %s [%s]" % (title_akas[country], country))
            
                db_title_aka = get_first_or_create_tag(
                    TitleAka, title=title_akas[country]
                )

                if db_title_aka.country:
                    if db_title_aka.country != country:
                        # El problema aqui es que el aka deberia permitir varios paises... 
                        # pero tenemos un poco en el aire que hacemos con TitleAka (yo 
                        # ultimamente pienso que tendriamos que borrarla... asi que por 
                        # ahora solo informamos en modo debug)
                        trace.debug("Tenemos este titulo como aka con distinto pais titulo:'%s' pais_db:'%s' pais_title:'%s'" % (
                            title_akas[country], db_title_aka.country, country
                        ))
                else:
                    db_title_aka.country = country
                    db_title_aka.save()
                
                movie.title_akas.add(db_title_aka)
            
            movie.save()
        
        trace.debug(" * Los titulos antiguos para la pelicula '%s' son:" % movie.title)
        trace.debug("    - %s: '%s'" % ('title', movie.title))
        trace.debug("    - %s: '%s'" % ('title_original', movie.title_original))
        trace.debug("    - %s: '%s'" % ('title_preferred', movie.title_preferred))
        
        if len(new_titles.keys()) == 3:
            trace.debug(" * Los titulos nuevos para la pelicula '%s' son:" % movie.title)
            trace.debug("    - %s: '%s'" % ('title', new_titles['title']))
            trace.debug("    - %s: '%s'" % ('title_original', new_titles['title_original']))
            trace.debug("    - %s: '%s'" % ('title_preferred', new_titles['title_preferred']))

            change_movie = False
            if movie.title != new_titles['title']:
                movie.title = new_titles['title']
                change_movie = True

            if movie.title_original != new_titles['title_original']:
                movie.title_original = new_titles['title_original']
                change_movie = True

            if movie.title_preferred != new_titles['title_preferred']:
                movie.title_preferred = new_titles['title_preferred']
                change_movie = True
            
            if change_movie:
                movie.save()

        else:
            trace.error("La pelicula '%s' no tiene titulos nuevos. [movie.id='%s']" % (movie.title, movie.id))
            if len(new_titles.keys()) > 0:
                trace.debug(" * Los titulos nuevos para la pelicula '%s' son:" % movie.title)
                if 'title' in new_titles:
                    trace.debug("    - %s: '%s'" % ('title', new_titles['title']))
                if 'title_original' in new_titles:
                    trace.debug("    - %s: '%s'" % ('title_original', new_titles['title_original']))
                if 'title_preferred' in new_titles:
                    trace.debug("    - %s: '%s'" % ('title_preferred', new_titles['title_preferred']))

