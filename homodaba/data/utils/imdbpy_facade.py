from django.db.models import Q
from django.utils.text import slugify

from data.models import Movie, MovieStorageType, ImdbCache

from imdb import IMDb

import pickle
import re

IMDB_API = IMDb(reraiseExceptions=True)

import codecs

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

def facade_search(title, year, title_alt=None, director=None, storage_type=None, 
    storage_name=None, path=None, imdb_id=None):
    """
    Funcion principal de busqueda que se encarga de hacerlo tanto
    en local como en imdb.
    Devuelve un FacadeResult si ha encontrado alguna coincidencia
    en cualquier otro caso devuelve None
    """

    # Buscamos por imdb_id primero (easy)
    if not imdb_id is None:
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

    # print(movies_local_data)

    if movies_local_data.count() == 1:
        facade_result = FacadeResult()
        facade_result.is_local_data = True
        facade_result.movie_match = True
        facade_result.movie = movies_local_data[0]

        return facade_result

    imdb_movie = search_movie_imdb(title, year, title_alt=title_alt, director=director)
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

def match_movie_by_director(search_results, director, year):
    slugify_directors = []
    for director_name in director.split(','):
        slugify_directors.append(clean_string(director_name))
        # Añadimos el director con "Nombre Apellidos" como "Apellidos Nombre" para direcores asiáticos
        slugify_directors.append(clean_string(reverse_name(director_name)))

    # TODO: traza print(slugify_directors)

    for sr in search_results:
        movie = get_imdb_movie(sr.movieID)
        if 'director' in movie.keys():
            movie_directors = [clean_string(p['name']) for p in movie['director']]

            # TODO: traza print(movie_directors)
            # Con que coincida un director damos la pelicula como buena
            for slugify_director in slugify_directors:
                if slugify_director in movie_directors and 'year' in movie and int(movie['year']) == int(year):
                    return movie
    
    # Llegados a este punto no hemos encontrado ninguna coincidencia decente
    # asi que lo damos por perdido
    return None


def match_movie(search_results, title, year, director=None):
    slugify_title = clean_string(title)
    matches = []
    matches_tier1 = []
    
    for sr in search_results:
        if 'year' in sr and int(sr['year']) == int(year) and clean_string(sr['title']) == slugify_title:
            # sr.keys()[0] == 'title', es para evitar talk-shows y otros programas 
            # especiales... por lo visto en ellos no mete primero el title
            if sr.keys()[0] == 'title':
                matches_tier1.append(sr)
            else:
                matches.append(sr)
    
    # Si solo hemos encontrado un tier1 asumimos que es el bueno
    if len(matches_tier1) == 1:
        return get_imdb_movie(matches_tier1[0].movieID)

    # Sumamos todos los matches dando prioridad por tier
    matches = matches_tier1 + matches

    total_matches = len(matches)

    # Si hay mas de un match, buscamos por director en los matches
    if total_matches > 1:
        return match_movie_by_director(matches, director, year)
    
    if total_matches == 0:
        movie = match_movie_by_director(search_results, director, year)
        if movie:
            return movie
        else:
            print("NO se han encontrado resultados en el IMDB para titulo identico %s (%s) - %s" % (title, year, director))
            trace_results(search_results)
            return None
    
    return get_imdb_movie(matches[0].movieID)

def trace_results(search_results):
    for sr in search_results:
        print("  - %s (%s) " % (sr['title'], sr['year'] if 'year' in sr and sr['year'] else 'None'))


def search_movie_imdb(title, year, title_alt=None, director=None):
    # Buscamos por titulo y año en IMDB
    search_results = search_imdb_movies('%s (%s)' % (title, year))

    if len(search_results) == 0:
        print(clean_string(title))
        search_results = search_imdb_movies('%s (%s)' % (clean_string(title), year))
    
    if len(search_results) == 0:
        search_results = search_imdb_movies(title)
    
    if len(search_results) == 0:
        search_results = search_imdb_movies(clean_string(title))
    
    # Si aun no lo encontramos por el titulo principal, 
    # buscamos por el alt (si lo tiene)
    if len(search_results) == 0 and title_alt:
        return search_movie_imdb(title_alt, year, director=director)
    
    if len(search_results) == 0:
        print("NO se han encontrado resultados en la busqueda IMDB para %s (%s)" % (title, year))
        return None
    
    # Buscamos el mas prometedor
    return match_movie(search_results, title, year, director)

def search_movie_local_data(title, year, title_alt=None):
    query_title = Q(title__iexact=title)
    query_title.add(Q(title_original__iexact=title), Q.OR)
    query_title.add(Q(title_preferred__iexact=title), Q.OR)

    if title_alt:
        query_title.add(Q(title__iexact=title_alt), Q.OR)
        query_title.add(Q(title_original__iexact=title_alt), Q.OR)
        query_title.add(Q(title_preferred__iexact=title_alt), Q.OR)

    query = Q(query_title)
    query_title.add(Q(year=year), Q.AND)
    
    # print(query)
    
    return Movie.objects.filter(query).all()
