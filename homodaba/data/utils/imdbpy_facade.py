from django.db.models import Q
from django.utils.text import slugify

from data.models import Movie, MovieStorageType, maybe_format_imdb_id
from .facade_model import FacadeMovie, is_valid_tmdb_movie
from .cache import add_cache, get_cache

import tmdbsimple as tmdb
import requests

import re

from . import Trace as trace

from homodaba.settings import TMDB_API_KEY

# kitty console:
# * OJO: para usar pixcat hay que instalarlo:
#   ~ pip install pixcat
# from pixcat import Image

# TMDB API
tmdb.API_KEY = TMDB_API_KEY
tmdb.REQUESTS_TIMEOUT = 5
tmdb.REQUESTS_SESSION = requests.Session()

"""
TODO: Revisar esta clases, lo mismo mover al modelo
"""
class FacadeResult:
    is_local_data = False
    storage_match = False
    movie: FacadeMovie|Movie = None
    local_movie: Movie = None
    facade_movie: FacadeMovie = None

    @staticmethod
    def local_data(movie, storage_match=False):
        facade_result = FacadeResult()
        facade_result.is_local_data = True
        facade_result.storage_match = storage_match
        facade_result.movie = movie
        facade_result.local_movie = movie

        return facade_result

    @staticmethod
    def facade_data(facade_movie, storage_match=False):
        facade_result = FacadeResult()
        facade_result.is_local_data = False
        facade_result.storage_match = storage_match
        facade_result.movie = facade_movie
        facade_result.facade_movie = facade_movie

        return facade_result

class FacadeMatch:
    is_a_match = False
    facade_movie = None
    promissing_facade_movies: list[FacadeMovie] = []

    @staticmethod
    def populate(facade_movie, promissing_facade_movies: list[FacadeMovie]=[]):
        facade_match = FacadeMatch()
        facade_match.is_a_match = facade_movie != None
        facade_match.facade_movie = facade_movie
        facade_match.promissing_facade_movies = promissing_facade_movies

        return facade_match

"""
TODO: funcion privada
"""
def is_match_facade_movie_by_id(facade_movie: FacadeMovie, facade_search_results: list[FacadeMovie]):
    for sr in facade_search_results:
        if (sr.imdb_id and sr.imdb_id == facade_movie.imdb_id) or \
            (sr.tmdb_id and sr.tmdb_id == facade_movie.tmdb_id):
            return True
    
    return False

"""
TODO: funcion privada
"""
def matchs_by_year_facade_movies(year, facade_movies: list[FacadeMovie], allow_almost_year=False):
    facade_result_year_matches: list[FacadeMovie] = []

    for facade_movie in facade_movies:
        if facade_movie.year == int(year):
            facade_result_year_matches.append(facade_movie)
        
        if allow_almost_year and (facade_movie.year - 1) == int(year):
            facade_result_year_matches.append(facade_movie)
        
    return facade_result_year_matches


# kitty console:
# def show_imdb_movie_image(imdb_movie):
#    if 'full-size cover url' in imdb_movie.keys() and imdb_movie['full-size cover url']:
#        Image(imdb_movie['full-size cover url']).thumbnail(128).show(align="left")
# Ademas de con pixcat, mucho mas sencillo seria hacerlo con un comando directo:
# import os
# os.system("kitty +kitten icat %s" % movie['full-size cover url'])

"""
Busca resultados exactos o prometedores en la API

Devuelve un FacadeMatch con los resultados
"""
def match_facade_movie(title, year=None, title_alt=None, director=None):
    facade_movie_results = search_facade_movies_by_title_and_year(title, year=year)

    if not facade_movie_results and title_alt:
        facade_movie_results = search_facade_movies_by_title_and_year(title_alt, year=year)

    if not facade_movie_results:
        return FacadeMatch.populate(None, facade_movie_results)

    trace.debug("match_facade_movie('%s', 'year=%s', 'title_alt=%s', 'director=%s')" % (
        title, year, title_alt, director)
    )

    trace_results(facade_movie_results)

    # Matches por year:
    facade_result_year_matches = []
    is_match_by_year = False
    if year:
        facade_result_year_matches = matchs_by_year_facade_movies(
            year=year, facade_movies=facade_movie_results, allow_almost_year=True
        )
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
    facade_director_matches: list[FacadeMovie] = []

    if not director is None and is_match_by_year:
        facade_director_matches = match_imdb_movie_by_director(facade_result_year_matches, director)
        director_movie_matches: list[FacadeMovie] = []

        for facade_movie in facade_director_matches:
            director_movie_matches.append(facade_movie)
        
        # Si encuentra solo uno, lo damos por bueno (ver comentario de arriba)
        if len(director_movie_matches) == 1:
            return FacadeMatch.populate(director_movie_matches[0], facade_movie_results)

    # Matches por titulo
    facade_title_matches: list[FacadeMovie] = []
    slugify_title = clean_string(title)

    title_movie_matches: list[FacadeMovie] = []

    for facade_movie in facade_clean_matches:
        if clean_string(facade_movie.title) == slugify_title:
            if facade_movie.kind == Movie.MK_MOVIE:
                # Solo si hemos encontrado con año
                if is_match_by_year:
                    title_movie_matches.append(facade_movie)
            facade_title_matches.append(facade_movie)

    # Si tenemos solo un match con year, titulo y es una peli valida lo damos
    # por bueno
    if len(title_movie_matches) == 1:
        return FacadeMatch.populate(title_movie_matches[0], facade_movie_results)

    # Si no hemos encontrado ningun match por titulo, buscamos en los akas
    # de los mas prometedores (esto puede tardar un wevete dependiendo
    # del numero de elementos)
    if len(facade_title_matches) == 0 or title_alt:
        clean_titles = [slugify_title]
        if title_alt:
            clean_titles.append(clean_string(title_alt))

        for facade_movie in facade_clean_matches:
            # Si el titulo ya esta en title_matches pasamos al siguiente
            if is_match_facade_movie_by_id(facade_movie, facade_title_matches):
                continue
            
            for clean_title in clean_titles:
                is_aka_match = False

                if len(facade_movie.title_akas) > 0:
                    for aka in facade_movie.title_akas:
                        if aka == clean_title:
                            facade_title_matches.append(facade_movie)
                            title_movie_matches.append(facade_movie)
                            is_aka_match = True
                            break
                
                if is_aka_match:
                    break

    # Si tenemos solo un match con year, titulo (ahora por los akas) y 
    # es una peli valida lo damos por bueno
    if is_match_by_year and len(title_movie_matches) == 1:
        return FacadeMatch.populate(title_movie_matches[0], facade_movie_results)

    if len(facade_title_matches) > 0:
        facade_clean_matches = facade_title_matches

    # Buscamos matches que sean solo de los tipos que nos interesen
    facade_movie_matches: list[FacadeMovie] = []
    other_matches: list[FacadeMovie] = []

    facade_movie_matches = facade_clean_matches

    # Si solo hemos encontrado un facade_movie_matches asumimos que es el bueno 
    # (si pusimos year)
    if is_match_by_year and len(facade_movie_matches) == 1:
        return FacadeMatch.populate(facade_movie_matches[0], facade_movie_results)
    
    # llegados a este punto, pueden haber ocurrido varias cosas:
    #   - El titulo es muy generico y devuelve demasiados matches
    #   - Algun dato de los introducidos esta mal
    #   - La busqueda de imdb deja mucho que desear (try google.com)
    # En resumen, no sabemos como continuar asi que devolvemos
    # una lista completando con las listas que hemos sacado
    # intentando ordenar por los mas prometedores
    promisings: list[FacadeMovie] = []

    # Ordenamos primero por los ultimos matches (facade_movie_matches)
    # Como segunda opcion tenemos los de director
    # Como tercera opcion other_matches
    # Por ultimo cogemos el resto de matches
    for facade_movie in facade_movie_matches + facade_director_matches + other_matches + facade_movie_results:
        if not is_match_facade_movie_by_id(facade_movie, promisings):
            promisings.append(facade_movie)

    return FacadeMatch.populate(None, promisings)

def get_facade_movie(imdb_id=None, tmdb_id=None):
    if not imdb_id and not tmdb_id:
        return None
    
    cache_key = "gfm(%s)" % (
        "imdb:%s" % imdb_id if imdb_id else "tmdb:%s" % tmdb_id
    )
    if cached_obj := get_cache(key=cache_key):
        return cached_obj
    
    tmdb_movie = get_tmdb_movie(tmdb_id=tmdb_id) if tmdb_id else None

    if imdb_id and not tmdb_movie:
        find_results = tmdb.Find(id=imdb_id).info(external_source='imdb_id')
        if 'movie_results' in find_results:
            if len(find_results['movie_results']) < 1 or not 'id' in find_results['movie_results'][0] \
                or len(find_results['movie_results']) > 1:
                return None
            
            tmdb_id = find_results['movie_results'][0]['id']

            tmdb_movie = get_tmdb_movie(tmdb_id=tmdb_id) if tmdb_id else None
    
    if not tmdb_movie or not is_valid_tmdb_movie(tmdb_movie):
        return None
    
    facade_movie = convert_tmdb_movie2facade_movie(tmdb_movie)
    
    return add_cache(key=cache_key, value=facade_movie)

"""
TODO: funcion privada
"""
def get_tmdb_movie(tmdb_id):
    return tmdb.Movies(tmdb_id)

"""
TODO: funcion privada
"""
def convert_tmdb_movie2facade_movie(tmdb_movie):
    fm = FacadeMovie()
    fm.populate_from_tmdb_movie(tmdb_movie)
    return fm

"""
TODO: funcion privada
"""
def search_facade_movies(search_query, title=None, year=None):
    cache_key = 'sim(%s)' % search_query
    if cached_obj := get_cache(key=cache_key):
        return cached_obj
    
    imdb_results: list[FacadeMovie] = []

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
        tmdb_movie = get_tmdb_movie(sr['id'])
        
        if is_valid_tmdb_movie(tmdb_movie):
            imdb_results.append(
                convert_tmdb_movie2facade_movie(tmdb_movie)
            )

    return add_cache(key=cache_key, value=imdb_results)

def clean_string(value):
    s = re.sub(r'[\.:;,\-\[\]\(\)\{\}¿¡]+', ' ', value)
    return re.sub(r'-', ' ', slugify(s))

"""
TODO: Ojo con esta func, no me gusta que devuelva dos tipos de objeto distintos... cuidadito
"""
def facade_get(imdb_id=None, tmdb_id=None, exclude_local_data=False):
    if not imdb_id and not tmdb_id:
        return FacadeResult.facade_data(None)
    
    movies_local_data = []

    if not exclude_local_data:
        if imdb_id:
            movies_local_data = Movie.objects.filter(imdb_id=imdb_id).all()
        
        if tmdb_id and not movies_local_data:
            movies_local_data = Movie.objects.filter(tmdb_id=tmdb_id).all()
    
    if movies_local_data.count() == 1:
        return FacadeResult.local_data(movies_local_data[0])
    else:
        return FacadeResult.facade_data(get_facade_movie(imdb_id=imdb_id, tmdb_id=tmdb_id))

def facade_search(title, year, title_alt=None, director=None, storage_type=None, 
    storage_name=None, path=None, imdb_id=None, tmdb_id=None, not_an_imdb_movie=False, exclude_local_data=False):
    """
    Funcion principal de busqueda que se encarga de hacerlo tanto
    en local como en imdb.
    Devuelve un FacadeResult si ha encontrado alguna coincidencia
    en cualquier otro caso devuelve None
    """

    facade_result = None

    # Buscamos por imdb_id o tmdb_id primero (easy)
    if imdb_id:
        imdb_id = maybe_format_imdb_id(imdb_id)
        trace.debug('\t\t- Buscando por imdb_id "%s"...' % imdb_id)
        facade_result = facade_get(imdb_id=imdb_id)

    if tmdb_id and not facade_result:
        trace.debug('\t\t- Buscando por tmdb_id "%s"...' % tmdb_id)
        facade_result = facade_get(tmdb_id=tmdb_id)

    if facade_result:
        return facade_result

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
    
    trace.debug('\t\t- Buscando en api externa "title=%s year=%s title_alt=%s director=%s"...' % (title, year, title_alt, director))
    facade_match = match_facade_movie(
        title, year, title_alt=title_alt, 
        director=director
    )

    if facade_match:
        if facade_match.facade_movie:
            kargs = {}

            if facade_match.facade_movie.imdb_id:
                kargs['imdb_id'] = facade_match.facade_movie.imdb_id
            if facade_match.facade_movie.tmdb_id:
                kargs['tmdb_id'] = facade_match.facade_movie.tmdb_id
            
            # Por ultima vez comprobamos que no la tenemos dada de alta en local
            local_movies = Movie.objects.filter(**kargs).all() if kargs else []

            if local_movies.count() == 0:
                return FacadeResult.facade_data(facade_match.facade_movie)

            return FacadeResult.local_data(local_movies[0])

        if facade_match.promissing_facade_movies:
            # Llegados a este punto no hemos encontrado ninguna coincidencia decente
            # sacamos un mensaje y devolvemos None
            trace.debug(" * No encontramos coincidencia clara para la peli '%s (%s)' *" % (title, year))
            trace.debug(" * Aunque hemos encontrado las siguientes: *")
            trace_results(facade_match.promissing_facade_movies)

    return None

"""
TODO: funcion privada
"""
def reverse_name(name):
    first = name.split()[0]
    second = " ".join(name.split()[1::])
    reverse_name = " ".join([second, first])
    return reverse_name

"""
TODO: funcion privada
"""
def slugify_directors(director_field):
    directors: list[str] = []

    if director_field:
        for director_name in director_field.split(','):
            directors.append(clean_string(director_name))
            # TODO: Esto es posible que no sea ya necesario... Investigar
            # Añadimos el director con "Nombre Apellidos" como "Apellidos Nombre" para directores asiáticos
            directors.append(clean_string(reverse_name(director_name)))
    
    return directors

"""
TODO: funcion privada
"""
def match_imdb_movie_by_director(facade_search_results: list[FacadeMovie], director):
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
    
    ssddss = slugify_directors(director)

    for slugify_director in ssddss:
        if slugify_director in movie_directors:
            return True
    
    trace.debug("SLUGIFY INPUT DIRECTORS:")
    trace.debug(ssddss)
    trace.debug("SLUGIFY IMDB DIRECTORS:")
    trace.debug(movie_directors)

    return False

"""
TODO: funcion privada
"""
def trace_results(facade_search_results):
    if trace.is_debug():
        for sr in facade_search_results:
            trace.debug("  - %s (%s) [%s] https://www.imdb.com/title/%s" % (sr.title, sr.year, sr.imdb_id, sr.imdb_id))
            # kitty console:
            # show_imdb_movie_image(movie)

"""
TODO: funcion privada
"""
def search_facade_movies_by_title_and_year(title, year=None):
    search_results: list[FacadeMovie] = []
    clean_title = clean_string(title)

    if year:
        # Buscamos por titulo y año en IMDB
        trace.debug('\t\t\t- Buscando en api externa por titulo y año "title=%s year=%s"...' % (title, year))
        search_results = search_facade_movies(search_query=title, title=title, year=year)

        if not search_results:
            trace.debug('\t\t\t- Buscando en api externa por titulo limpio y año "clean_title=%s year=%s"...' % (clean_title, year))
            search_results = search_facade_movies(search_query=clean_title, title=clean_title, year=year)
        
        if not search_results:
            trace.debug('\t\t\t- Buscando en api externa por titulo en query y año "title=%s year=%s"...' % (title, year))
            search_results = search_facade_movies(search_query=title, year=year)

        if not search_results:
            trace.debug('\t\t\t- Buscando en api externa por titulo limpio en query y año "clean_title=%s year=%s"...' % (clean_title, year))
            search_results = search_facade_movies(search_query=clean_title, year=year)
    
    if not search_results:
        trace.debug('\t\t\t- Buscando en api externa por titulo "title=%s"...' % title)
        search_results = search_facade_movies(title, title=title)
    
    if not search_results:
        trace.debug('\t\t\t- Buscando en api externa por titulo limpio "clean_string(title)=%s"...' % clean_string(title))
        search_results = search_facade_movies(clean_title, title=clean_title)

    if not search_results:
        trace.debug('\t\t\t- Buscando en api externa por titulo en search_query "title=%s"...' % title)
        search_results = search_facade_movies(title)
    
    if not search_results:
        trace.debug('\t\t\t- Buscando en api externa por titulo limpio en search_query "clean_title=%s"...' % clean_string(title))
        search_results = search_facade_movies(clean_title)
    
    if not search_results:
        trace.debug("NO se han encontrado resultados en la busqueda IMDB para %s (%s)" % (title, year))
    
    return search_results

"""
TODO: funcion privada
"""
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
