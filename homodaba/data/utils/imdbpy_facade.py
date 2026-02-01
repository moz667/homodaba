from django.db.models import Q
from django.utils.text import slugify

from data.models import Movie, MovieStorageType, get_imdb_cache_objects
from .facade_model import FacadeMovie

import tmdbsimple as tmdb
import requests

import pickle
import re

import codecs

from . import Trace as trace

from homodaba.settings import NO_CACHE, UPDATE_CACHE, TMDB_API_KEY

# kitty console:
# * OJO: para usar pixcat hay que instalarlo:
#   ~ pip install pixcat
# from pixcat import Image

# TMDB API
tmdb.API_KEY = TMDB_API_KEY
tmdb.REQUESTS_TIMEOUT = 5
tmdb.REQUESTS_SESSION = requests.Session()

IMDB_CACHE_OBJS = get_imdb_cache_objects()

"""
TODO: Hay un poco de chocho con search_movie_imdb y search_imdb_movies... revisar/refactorizar... :P
"""

def match_imdb_id(imdb_id, facade_search_results):
    for sr in facade_search_results:
        if sr.imdb_id == imdb_id:
            return True
    
    return False

def facade_result_match_imdb_year(year, facade_search_results):
    facade_result_year_matches = []

    for sr in facade_search_results:
        if sr.year == int(year):
            facade_result_year_matches.append(sr)
        
    return facade_result_year_matches


# kitty console:
# def show_imdb_movie_image(imdb_movie):
#    if 'full-size cover url' in imdb_movie.keys() and imdb_movie['full-size cover url']:
#        Image(imdb_movie['full-size cover url']).thumbnail(128).show(align="left")
# Ademas de con pixcat, mucho mas sencillo seria hacerlo con un comando directo:
# import os
# os.system("kitty +kitten icat %s" % movie['full-size cover url'])

"""
Busca resultados exactos o prometedores en imdb

@return:
    imdb_movie, un resultado de tipo Cinemagoer.Movie o None si no consigue encontrar uno exacto
    promisings, lista con search results prometedores (ver search_imdb_movies)
"""
def match_facade_movie(title, year=None, title_alt=None, director=None):
    facade_movie_results = search_movie_imdb(title, year=year, title_alt=title_alt, director=director)

    # TODO: si no encuentra nada con esta busqueda... que podemos hacer?
    if not facade_movie_results or len(facade_movie_results) == 0:
        return None, []

    trace.debug("match_facade_movie('%s', 'year=%s', 'title_alt=%s', 'director=%s')" % (
        title, year, title_alt, director)
    )

    trace_results(facade_movie_results)

    # Matches por year:
    facade_result_year_matches = facade_result_match_imdb_year(year=year, facade_search_results=facade_movie_results) if year else []
    is_match_by_year = len(facade_result_year_matches) > 0

    # Lista temporal donde vamos poniendo los mas prometedores
    # Si tenemos year_matches, pues ya hemos reducido... si no por defecto 
    # los resultados de la busqueda de imdb
    facade_clean_matches = facade_result_year_matches if is_match_by_year else facade_movie_results
    
    # Matches por director:
    # Esta logica es un poco raruna pero funciona bien:
    # Es mas facil encontrar una peli por año y director que por titulo y año
    # Si el director coincide y el año tambien, es muy probable que sea match
    # sobre todo si es solo un resultado, ya que un director es raro que 
    # trabaje en mas de una peli que nos haya sido devuelta por la busqueda
    # de imdb y filtrado por año
    facade_director_matches = []

    if not director is None and is_match_by_year:
        facade_director_matches = match_imdb_movie_by_director(facade_result_year_matches, director)
        director_movie_matches = []

        for facade_movie in facade_director_matches:
            if is_valid_imdb_movie(facade_movie):
                director_movie_matches.append(facade_movie)
        
        # Si encuentra solo uno, lo damos por bueno (ver comentario de arriba)
        if len(director_movie_matches) == 1:
            return director_movie_matches[0], facade_movie_results

    # Matches por titulo
    facade_title_matches = []
    slugify_title = clean_string(title)

    title_movie_matches = []

    for facade_movie in facade_clean_matches:
        if clean_string(facade_movie.title) == slugify_title:
            if facade_movie.kind == Movie.MK_MOVIE:
                # Solo si hemos encontrado con año
                if is_match_by_year:
                    if is_valid_imdb_movie(facade_movie):
                        title_movie_matches.append(facade_movie)
            facade_title_matches.append(facade_movie)

    # Si tenemos solo un match con year, titulo y es una peli valida lo damos
    # por bueno
    if len(title_movie_matches) == 1:
        return title_movie_matches[0], facade_movie_results

    # Si no hemos encontrado ningun match por titulo, buscamos en los akas
    # de los mas prometedores (esto puede tardar un wevete dependiendo
    # del numero de elementos)
    if len(facade_title_matches) == 0 or title_alt:
        clean_titles = [slugify_title]
        if title_alt:
            clean_titles.append(clean_string(title_alt))

        for facade_movie in facade_clean_matches:
            # Si el titulo ya esta en title_matches pasamos al siguiente
            if match_imdb_id(facade_movie.imdb_id, facade_title_matches):
                continue
            
            for clean_title in clean_titles:
                is_aka_match = False

                if len(facade_movie.title_akas) > 0:
                    for aka in facade_movie.title_akas:
                        if aka == clean_title:
                            facade_title_matches.append(facade_movie)

                            if is_valid_imdb_movie(facade_movie):
                                title_movie_matches.append(facade_movie)
                            is_aka_match = True
                            break
                
                if is_aka_match:
                    break

    # Si tenemos solo un match con year, titulo (ahora por los akas) y 
    # es una peli valida lo damos por bueno
    if is_match_by_year and len(title_movie_matches) == 1:
        return title_movie_matches[0], facade_movie_results

    if len(facade_title_matches) > 0:
        facade_clean_matches = facade_title_matches

    # Buscamos matches que sean solo de los tipos que nos interesen
    facade_movie_matches = []
    other_matches = []

    facade_movie_matches = facade_clean_matches

    # Si solo hemos encontrado un facade_movie_matches asumimos que es el bueno 
    # (si pusimos year)
    if is_match_by_year and len(facade_movie_matches) == 1:
        facade_movie = facade_movie_matches[0]

        if is_valid_imdb_movie(facade_movie):
            return facade_movie, facade_movie_results
    
    # llegados a este punto, pueden haber ocurrido varias cosas:
    #   - El titulo es muy generico y devuelve demasiados matches
    #   - Algun dato de los introducidos esta mal
    #   - La busqueda de imdb deja mucho que desear (try google.com)
    # En resumen, no sabemos como continuar asi que devolvemos
    # una lista completando con las listas que hemos sacado
    # intentando ordenar por los mas prometedores
    promisings = []

    # Ordenamos primero por los ultimos matches (facade_movie_matches)
    for sr in facade_movie_matches:
        promisings.append(sr)
    
    # Como segunda opcion tenemos los de director
    for sr in facade_director_matches:
        promisings.append(sr) if not match_imdb_id(sr.imdb_id, promisings) else None

    # Como tercera opcion other_matches
    for sr in other_matches:
        promisings.append(sr) if not match_imdb_id(sr.imdb_id, promisings) else None

    # Por ultimo cogemos el resto de matches
    for sr in facade_movie_results:
        promisings.append(sr) if not match_imdb_id(sr.imdb_id, promisings) else None

    return None, promisings

def serialize(obj):
    return codecs.encode(pickle.dumps(obj), "base64").decode()

def unserialize(str_obj):
    return pickle.loads(codecs.decode(str_obj.encode(), "base64"))

def get_aka_type_and_value(title_aka_raw):
    # World-wide (English title)
    matches = re.search('( World-wide \(.*\))$', title_aka_raw)

    # (original title)
    if not matches:
        matches = re.search('( \(.*\))$', title_aka_raw)

    if matches:
        title_type_match = matches.group(0)
        title_type_clean = title_type_match.replace('(', '').replace(')', '')
        title_aka_clean = title_aka_raw.replace(title_type_match, '')

        return title_type_clean, title_aka_clean
    
    return None, title_aka_raw

def is_spanish_country(country):
    spanish_language_countries = [
        'Mexico', 'Colombia', 'Spain', 'Argentina',
        'Peru', 'Venezuela', 'Chile', 'Guatemala',
        'Ecuador', 'Bolivia', 'Cuba',
        'Dominican Republic', 'Honduras', 'Paraguay',
        'El Salvador', 'Nicaragua', 'Costa Rica',
        'Panama', 'Uruguay', 'Equatorial Guinea',
    ]

    return country in spanish_language_countries

def get_facade_movie(imdb_id=None, tmdb_id=None):
    if not imdb_id and not tmdb_id:
        return None
    
    if not NO_CACHE:
        cache_data = IMDB_CACHE_OBJS.filter(imdb_id=imdb_id if not imdb_id is None else tmdb_id).all()

        if cache_data.count() > 0:
            if not UPDATE_CACHE:
                return unserialize(cache_data[0].raw_data)
            else:
                IMDB_CACHE_OBJS.filter(imdb_id=imdb_id if not imdb_id is None else tmdb_id).delete()
    
    facade_movie = FacadeMovie()

    if not imdb_id is None:
        find_results = tmdb.Find(id=imdb_id).info(external_source='imdb_id')
        if 'movie_results' in find_results:
            if len(find_results['movie_results']) < 1 or not 'id' in find_results['movie_results'][0]:
                raise Exception(message="Movie not found on find by imdb_id")
            elif len(find_results['movie_results']) > 1:
                raise Exception(message="Too many results on find by imdb_id")
            
            tmdb_id = find_results['movie_results'][0]['id']

    facade_movie = convert_tmdb_movie2facade_movie(get_tmdb_movie(tmdb_id=tmdb_id))
    
    if not NO_CACHE or UPDATE_CACHE:
        IMDB_CACHE_OBJS.create(
            imdb_id=imdb_id if not imdb_id is None else tmdb_id,
            raw_data=serialize(facade_movie)
        )

    return facade_movie

def get_tmdb_movie(tmdb_id):
    # TODO: Cachear...
    return tmdb.Movies(tmdb_id)

def convert_tmdb_movie2facade_movie(tmdb_movie):
    fm = FacadeMovie()
    fm.populate_from_tmdb_movie(tmdb_movie)
    return fm

def search_imdb_movies(search_query, title=None, year=None):
    if not NO_CACHE:
        cache_data = IMDB_CACHE_OBJS.filter(search_query=search_query).all()

        if cache_data.count() > 0:
            if not UPDATE_CACHE:
                return unserialize(cache_data[0].raw_data)
            else:
                IMDB_CACHE_OBJS.filter(search_query=search_query).delete()
    
    imdb_results = []

    search = tmdb.Search()
    if not title is None and not year is None:
        response = search.movie(query=search_query, title=title, year=year)
    elif not title is None:
        response = search.movie(query=search_query, title=title)
    elif not year is None:
        response = search.movie(query=search_query, year=year)
    else:
        response = search.movie(query=search_query)

    for sr in search.results:
        imdb_results.append(
            convert_tmdb_movie2facade_movie(get_tmdb_movie(sr['id']))
        )
    
    if not NO_CACHE or UPDATE_CACHE:
        IMDB_CACHE_OBJS.create(
            search_query=search_query,
            raw_data=serialize(imdb_results)
        )

    return imdb_results


class FacadeResult:
    is_local_data = False
    is_imdb_data = False
    storage_match = False
    movie = None
    posible_movies = [] # Candidatas posibles

    @staticmethod
    def local_data(movie, storage_match=False):
        facade_result = FacadeResult()
        facade_result.is_local_data = True
        facade_result.storage_match = storage_match
        facade_result.movie = movie

        return facade_result

    @staticmethod
    def imdb_data(facade_movie, storage_match=False):
        facade_result = FacadeResult()
        facade_result.is_local_data = False
        facade_result.storage_match = storage_match
        facade_result.movie = facade_movie

        return facade_result

def clean_string(value):
    s = re.sub(r'[\.:;,\-\[\]\(\)\{\}¿¡]+', ' ', value)
    return re.sub(r'-', ' ', slugify(s))

def facade_get(imdb_id, exclude_local_data=False):
    movies_local_data = Movie.objects.filter(imdb_id=imdb_id).all() if not exclude_local_data else []
    
    if movies_local_data.count() == 1:
        return FacadeResult.local_data(movies_local_data[0])
    else:
        return FacadeResult.imdb_data(get_facade_movie(imdb_id=imdb_id))

def facade_search(title, year, title_alt=None, director=None, storage_type=None, 
    storage_name=None, path=None, imdb_id=None, not_an_imdb_movie=False, exclude_local_data=False):
    """
    Funcion principal de busqueda que se encarga de hacerlo tanto
    en local como en imdb.
    Devuelve un FacadeResult si ha encontrado alguna coincidencia
    en cualquier otro caso devuelve None
    """

    # Buscamos por imdb_id primero (easy)
    if imdb_id:
        trace.debug('\t\t- Buscando por imdb_id "%s"...' % imdb_id)
        return facade_get(imdb_id)
    
    if not exclude_local_data:
        # Para buscar datos locales es mas sencillo encontrar primero por ubicacion
        # si se trata de una peli almacenada en el disco
        if storage_type and storage_name and path:
            trace.debug('\t\t- Buscando por storage "storage_type=%s storage_name=%s path=%s"...' % (storage_type, storage_name, path))
            storages = MovieStorageType.objects.filter(
                storage_type=storage_type, 
                name=storage_name,
                path=path,
            )

            if storages.count() == 1:
                return FacadeResult.local_data(storages[0].movie, storage_match=True)

        # Las que no podemos buscar por la ubicacion del archivo, la buscamos por 
        # los campos tipicos de titulo y año
        trace.debug('\t\t- Buscando datos locales "title=%s year=%s title_alt=%s)"...' % (title, year, title_alt))
        movies_local_data = search_movie_local_data(title, year, title_alt)

        if movies_local_data.count() == 1:
            return FacadeResult.local_data(movies_local_data[0])
        elif movies_local_data.count() > 1:
            trace.debug(" * Hemos encontrado varios resultados para la busqueda local (title='%s', year='%s', title_alt='%s')" % (title, year, title_alt))
        
        # Si se trata de una peli que no esta en el imdb, no la vamos a buscar alli
        if not_an_imdb_movie:
            trace.debug(" * La pelicula '%s (%s)' se trata de una pelicula que no se encuentra en el imdb y que todavia no hemos dado de alta." % (title, year))
            return None
    
    trace.debug('\t\t- Buscando en imdb "title=%s year=%s title_alt=%s director=%s"...' % (title, year, title_alt, director))
    facade_movie, facade_search_results = match_facade_movie(
        title, year, title_alt=title_alt, 
        director=director
    )

    if not facade_movie is None:
        # Por ultima vez comprobamos que no la tenemos dada de alta en local
        local_movies = Movie.objects.filter(imdb_id=facade_movie.imdb_id).all()

        if local_movies.count() == 0:
            return FacadeResult.imdb_data(facade_movie)

        return FacadeResult.local_data(local_movies[0])
    
    if facade_search_results is None or len(facade_search_results) == 0:
        return None
    

    # Llegados a este punto no hemos encontrado ninguna coincidencia decente
    # sacamos un mensaje y devolvemos None
    trace.debug(" * No encontramos coincidencia clara para la peli '%s (%s)' *" % (title, year))
    trace.debug(" * Aunque hemos encontrado las siguientes: *")
    trace_results(facade_search_results)

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
            # Añadimos el director con "Nombre Apellidos" como "Apellidos Nombre" para directores asiáticos
            directors.append(clean_string(reverse_name(director_name)))
    
    return directors

def match_imdb_movie_by_director(facade_search_results, director):
    matches = []

    for facade_movie in facade_search_results:
        if len(facade_movie.directors) > 0:
            # Con que coincida un director damos la pelicula como buena
            if match_director(director, facade_movie.directors):
                matches.append(facade_movie)
    
    # Llegados a este punto no hemos encontrado ninguna coincidencia decente
    # asi que lo damos por perdido
    return matches

def match_director(director, facade_credit_directors):
    movie_directors = [clean_string(p.name) for p in facade_credit_directors]

    for p in facade_credit_directors:
        if p.canonical_name:
            movie_directors.append(clean_string(p.canonical_name))
    
    slugify_directors = slugify_directors(director)

    for slugify_director in slugify_directors:
        if slugify_director in movie_directors:
            return True
    
    trace.debug("SLUGIFY INPUT DIRECTORS:")
    trace.debug(slugify_directors)
    trace.debug("SLUGIFY IMDB DIRECTORS:")
    trace.debug(movie_directors)

    return False

def is_valid_imdb_movie(facade_movie: FacadeMovie):
    if facade_movie.kind is None:
        return False
    elif facade_movie.kind != Movie.MK_MOVIE:
        return False
    
    if facade_movie.poster_url is None:
        return False
    
    return True

def trace_results(facade_search_results):
    if trace.is_debug():
        for sr in facade_search_results:
            trace.debug("  - %s (%s) [%s] https://www.imdb.com/title/tt%s" % (sr.title, sr.year, sr.imdb_id, sr.imdb_id))
            # kitty console:
            # show_imdb_movie_image(movie)

def search_movie_imdb(title, year=None, title_alt=None, director=None):
    search_results = None
    clean_title = clean_string(title)

    if title and year:
        # Buscamos por titulo y año en IMDB
        trace.debug('\t\t\t- Buscando en imdb por titulo y año "title=%s year=%s"...' % (title, year))
        search_results = search_imdb_movies(search_query=title, title=title, year=year)

        if search_results is None or len(search_results) == 0:
            trace.debug('\t\t\t- Buscando en imdb por titulo limpio y año "clean_title=%s year=%s"...' % (clean_title, year))
            search_results = search_imdb_movies(search_query=clean_title, title=clean_title, year=year)
        
        if search_results is None or len(search_results) == 0:
            trace.debug('\t\t\t- Buscando en imdb por titulo en query y año "title=%s year=%s"...' % (title, year))
            search_results = search_imdb_movies(search_query=title, year=year)

        if search_results is None or len(search_results) == 0:
            trace.debug('\t\t\t- Buscando en imdb por titulo limpio en query y año "clean_title=%s year=%s"...' % (clean_title, year))
            search_results = search_imdb_movies(search_query=title, year=year)
    
    if search_results is None or len(search_results) == 0:
        trace.debug('\t\t\t- Buscando en imdb por titulo "title=%s"...' % title)
        search_results = search_imdb_movies(title, title=title)
    
    if search_results is None or len(search_results) == 0:
        trace.debug('\t\t\t- Buscando en imdb por titulo limpio "clean_string(title)=%s"...' % clean_string(title))
        search_results = search_imdb_movies(clean_title, title=clean_title)

    if search_results is None or len(search_results) == 0:
        trace.debug('\t\t\t- Buscando en imdb por titulo en search_query "title=%s"...' % title)
        search_results = search_imdb_movies(title)
    
    if search_results is None or len(search_results) == 0:
        trace.debug('\t\t\t- Buscando en imdb por titulo limpio en search_query "clean_title=%s"...' % clean_string(title))
        search_results = search_imdb_movies(clean_title)
    
    # Si aun no lo encontramos por el titulo principal, 
    # buscamos por el alt (si lo tiene)
    # TODO: Revisar esto... no entiendo porque pero antes solo buscaba por 
    # title_alt si le habiamos pasado director:
    # if (search_results is None or len(search_results) == 0) and title_alt and not director is None:
    if (search_results is None or len(search_results) == 0) and title_alt:
        trace.debug('\t\t\t- Buscando en imdb por titulo alt, año y director "title_alt=%s year=%s director=%s)"...' % (title_alt, year, director))
        return search_movie_imdb(title_alt, year=year, director=director)
    
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
