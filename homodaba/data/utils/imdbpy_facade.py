from django.db.models import Q
from django.utils.text import slugify

from data.models import Movie, MovieStorageType, ImdbCache

from imdb import IMDb

import pickle
import re

IMDB_API = IMDb(reraiseExceptions=True)

import codecs

from . import Trace as trace

"""
TODO: Hay un poco de chocho con search_movie_imdb y search_imdb_movies... revisar/refactorizar... :P
"""

def serialize(obj):
    return codecs.encode(pickle.dumps(obj), "base64").decode()

def unserialize(str_obj):
    return pickle.loads(codecs.decode(str_obj.encode(), "base64"))

def get_imdb_movie(imdb_id):
    cache_data = ImdbCache.objects.filter(imdb_id=imdb_id).all()

    if cache_data.count() == 1:
        return unserialize(cache_data[0].raw_data)
    
    imdb_movie = IMDB_API.get_movie(imdb_id)

    ImdbCache.objects.create(
        imdb_id=imdb_id,
        raw_data=serialize(imdb_movie)
    )

    return imdb_movie

def search_imdb_movies(search_query):
    cache_data = ImdbCache.objects.filter(search_query=search_query).all()

    if cache_data.count() == 1:
        return unserialize(cache_data[0].raw_data)
    
    imdb_results = IMDB_API.search_movie(search_query)

    ImdbCache.objects.create(
        search_query=search_query,
        raw_data=serialize(imdb_results)
    )

    return imdb_results


class FacadeResult:
    is_local_data = False
    is_imdb_data = False
    storage_match = False
    movie_match = False
    movie = None

    @staticmethod
    def local_data(movie):
        facade_result = FacadeResult()
        facade_result.is_local_data = True
        facade_result.movie_match = True
        facade_result.movie = movie

        return facade_result

def clean_string(value):
    s = re.sub(r'[\.:;,\-\[\]\(\)\{\}¿¡]+', ' ', value)
    return re.sub(r'-', ' ', slugify(s))

def facade_get(imdb_id):
    movies_local_data = Movie.objects.filter(imdb_id=imdb_id).all()
    
    if movies_local_data.count() == 1:
        return FacadeResult.local_data(movies_local_data[0])
    else:
        # Esto siempre deberia devolver un resultado... si no lo devuelve es 
        # que el id esta mal :P
        imdb_movie = get_imdb_movie(imdb_id)

        facade_result = FacadeResult()
        facade_result.is_imdb_data = True
        facade_result.movie = imdb_movie

        return facade_result

def facade_search(title, year, title_alt=None, director=None, storage_type=None, 
    storage_name=None, path=None, imdb_id=None):
    """
    Funcion principal de busqueda que se encarga de hacerlo tanto
    en local como en imdb.
    Devuelve un FacadeResult si ha encontrado alguna coincidencia
    en cualquier otro caso devuelve None
    """

    # Buscamos por imdb_id primero (easy)
    if imdb_id:
        return facade_get(imdb_id)
    
    # Para buscar datos locales es mas sencillo encontrar primero por ubicacion
    # si se trata de una peli almacenada en el disco
    if storage_type and storage_name and path:
        storages = MovieStorageType.objects.filter(
            storage_type=storage_type, 
            name=storage_name,
            path=path,
        )

        if storages.count() == 1:
            facade_result = FacadeResult()
            facade_result.is_local_data = True
            facade_result.storage_match = True
            facade_result.movie = storages[0].movie

            return facade_result

    # Las que no podemos buscar por la ubicacion del archivo, la buscamos por 
    # los campos tipicos de titulo y año
    movies_local_data = search_movie_local_data(title, year, title_alt)

    if movies_local_data.count() == 1:
        facade_result = FacadeResult()
        facade_result.is_local_data = True
        facade_result.movie_match = True
        facade_result.movie = movies_local_data[0]

        return facade_result

    search_results = search_movie_imdb(title, year, title_alt=title_alt, director=director)

    if search_results is None or len(search_results) == 0:
        return None
    
    # Buscamos el mas prometedor
    imdb_movie = match_imdb_movie(search_results, title, year, director)

    if imdb_movie:
        facade_result = FacadeResult()
        # Por ultima vez comprobamos que no la tenemos dada de alta en local
        local_movies = Movie.objects.filter(imdb_id=imdb_movie.getID()).all()

        if local_movies.count() == 0:
            facade_result.is_imdb_data = True
            facade_result.movie = imdb_movie
        else:
            facade_result.is_local_data = True
            facade_result.movie = local_movies[0]
        
        return facade_result

    # Llegados a este punto no hemos encontrado ninguna coincidencia decente
    # asi que lo damos por perdido
    return None

def reverse_name(name):
    first = name.split()[0]
    second = " ".join(name.split()[1::])
    reverse_name = " ".join([second, first])
    return reverse_name

def slugify_directors(director_field):
    directors = []

    if director_field:
        for director_name in director_field.split(','):
            directors.append(clean_string(director_name))
            # Añadimos el director con "Nombre Apellidos" como "Apellidos Nombre" para direcores asiáticos
            directors.append(clean_string(reverse_name(director_name)))
    
    return directors

def match_imdb_movie_by_director(search_results, director, year):
    directors = slugify_directors(director)

    for sr in search_results:
        movie = get_imdb_movie(sr.movieID)
        if 'director' in movie.keys():
            movie_directors = [clean_string(p['name']) for p in movie['director']]

            # Con que coincida un director damos la pelicula como buena
            for slugify_director in directors:
                if slugify_director in movie_directors and 'year' in movie and int(movie['year']) == int(year):
                    return movie
    
    # Llegados a este punto no hemos encontrado ninguna coincidencia decente
    # asi que lo damos por perdido
    return None


def match_imdb_movie(search_results, title, year, director=None):
    slugify_title = clean_string(title)
    matches = []
    matches_tier1 = []
    
    trace.debug("match_imdb_movie(search_results, '%s', '%s', '%s'" % (title, year, director))
    trace_results(search_results)

    if not director is None:
        year_matches = []

        for sr in search_results:
            if 'year' in sr and sr['year'] and int(sr['year']) == int(year):
                year_matches.append(sr)

        movie = match_imdb_movie_by_director(year_matches, director, year)

        if movie:
            return movie

    for sr in search_results:
        if 'year' in sr and sr['year'] and int(sr['year']) == int(year) and clean_string(sr['title']) == slugify_title:
            # sr.keys()[0] == 'title', es para evitar talk-shows y otros programas 
            # especiales... por lo visto en ellos no mete primero el title
            if sr.keys()[0] == 'title':
                matches_tier1.append(sr)
            else:
                matches.append(sr)
    
    # Sumamos todos los matches dando prioridad por tier
    matches = matches_tier1 + matches

    # Si solo hemos encontrado un tier1 asumimos que es el bueno
    if len(matches_tier1) == 1:
        trace.debug(">>> Seleccionando: len(matches_tier1) == 1")
        trace_results(matches_tier1)
        return get_imdb_movie(matches_tier1[0].movieID)

    total_matches = len(matches)

    if not director is None:
        # Si hay mas de un match, buscamos por director en los matches
        if total_matches > 1:
            return match_imdb_movie_by_director(matches, director, year)
        
        if total_matches == 0:
            movie = match_imdb_movie_by_director(search_results, director, year)

            if movie:
                return movie
            else:
                trace.debug("NO se han encontrado resultados en el IMDB para titulo identico %s (%s) - %s" % (title, year, director))
                return None

    trace.debug(">>> Seleccionando: matches[0]")
    trace_results(matches)

    return get_imdb_movie(matches[0].movieID) if len(matches) > 0 else None

def trace_results(search_results):
    if trace.is_debug():
        for sr in search_results:
            trace.debug("  - %s (%s) [%s]" % (sr['title'], sr['year'] if 'year' in sr and sr['year'] else 'None', sr.movieID))
            movie = get_imdb_movie(sr.movieID)
            if 'director' in movie.keys():
                trace.debug("        DIRECTORES:")
                movie_directors = [clean_string(p['name']) for p in movie['director']]
                for director in movie_directors:
                    trace.debug("        * '%s'" % director)

def search_movie_imdb(title, year, title_alt=None, director=None):
    # Buscamos por titulo y año en IMDB
    search_results = search_imdb_movies('%s (%s)' % (title, year))

    if search_results is None or len(search_results) == 0:
        search_results = search_imdb_movies('%s (%s)' % (clean_string(title), year))
    
    if search_results is None or len(search_results) == 0:
        search_results = search_imdb_movies(title)
    
    if search_results is None or len(search_results) == 0:
        search_results = search_imdb_movies(clean_string(title))
    
    # Si aun no lo encontramos por el titulo principal, 
    # buscamos por el alt (si lo tiene)
    if (search_results is None or len(search_results) == 0) and title_alt and not director is None:
        return search_movie_imdb(title_alt, year, director=director)
    
    if search_results is None or len(search_results) == 0:
        trace.debug("NO se han encontrado resultados en la busqueda IMDB para %s (%s)" % (title, year))
        return None
    
    return search_results

def search_movie_local_data(title, year, title_alt=None, director=None):
    query_title = Q(title__iexact=title)
    query_title.add(Q(title_original__iexact=title), Q.OR)
    query_title.add(Q(title_preferred__iexact=title), Q.OR)

    if title_alt:
        query_title.add(Q(title__iexact=title_alt), Q.OR)
        query_title.add(Q(title_original__iexact=title_alt), Q.OR)
        query_title.add(Q(title_preferred__iexact=title_alt), Q.OR)

    query = Q(query_title)
    query_title.add(Q(year=year), Q.AND)
    
    matches_title_movies = Movie.objects.filter(query).all()

    if len(matches_title_movies) > 0 and director:
        ss_directors = slugify_directors(director)

        for movie in matches_title_movies:
            for director in movie.get_directors():
                for ss_director in ss_directors:
                    director_clean_names = []
                    
                    if director.person.name:
                        director_clean_names.append(clean_string(director.person.name))
                    
                    if director.person.canonical_name:
                        director_clean_names.append(clean_string(director.person.canonical_name))

                    if ss_director in director_clean_names:
                        return [movie]

    return matches_title_movies
