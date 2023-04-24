from django.db.models import Q
from django.utils.text import slugify

from data.models import Movie, MovieStorageType, get_imdb_cache_objects

from imdb import Cinemagoer

import pickle
import re

IMDB_API = Cinemagoer(reraiseExceptions=True)

import codecs
from enum import Enum

from . import Trace as trace

from homodaba.settings import IMDB_VALID_MOVIE_KINDS, NO_CACHE, UPDATE_CACHE

# kitty console:
# * OJO: para usar pixcat hay que instalarlo:
#   ~ pip install pixcat
# from pixcat import Image

IMDB_CACHE_OBJS = get_imdb_cache_objects()

"""
TODO: Hay un poco de chocho con search_movie_imdb y search_imdb_movies... revisar/refactorizar... :P
"""

def match_imdb_id(imdb_id, search_results):
    for sr in search_results:
        if sr.movieID == imdb_id:
            return True
    
    return False

def match_imdb_year(year, search_results):
    year_matches = []

    for sr in search_results:
        if 'year' in sr and sr['year'] and int(sr['year']) == int(year):
            year_matches.append(sr)
        
    return year_matches


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
def match_imdb_movie(title, year=None, title_alt=None, director=None, valid_kinds=IMDB_VALID_MOVIE_KINDS):
    search_results = search_movie_imdb(title, year=year, title_alt=title_alt, director=director)

    # TODO: si no encuentra nada con esta busqueda... que podemos hacer?
    if not search_results or len(search_results) == 0:
        return None, []

    trace.debug("match_imdb_movie('%s', 'year=%s', 'title_alt=%s', 'director=%s', valid_kinds=[%s])" % (
        title, year, title_alt, director, ','.join(valid_kinds))
    )

    trace_results(search_results, mini_info=True)

    # Matches por year:
    year_matches = match_imdb_year(year=year, search_results=search_results) if year else []
    is_match_by_year = len(year_matches) > 0

    # Lista temporal donde vamos poniendo los mas prometedores
    # Si tenemos year_matches, pues ya hemos reducido... si no por defecto 
    # los resultados de la busqueda de imdb
    clean_matches = year_matches if is_match_by_year else search_results
    
    # Matches por director:
    # Esta logica es un poco raruna pero funciona bien:
    # Es mas facil encontrar una peli por año y director que por titulo y año
    # Si el director coincide y el año tambien, es muy probable que sea match
    # sobre todo si es solo un resultado, ya que un director es raro que 
    # trabaje en mas de una peli que nos haya sido devuelta por la busqueda
    # de imdb y filtrado por año
    director_matches = []

    if not director is None and is_match_by_year:
        director_matches = match_imdb_movie_by_director(year_matches, director)
        director_movie_matches = []

        for sr in director_matches:
            imdb_movie = get_imdb_movie(sr.movieID)
            if is_valid_imdb_movie(imdb_movie, valid_kinds=valid_kinds):
                director_movie_matches.append(imdb_movie)
        
        # Si encuentra solo uno, lo damos por bueno (ver comentario de arriba)
        if len(director_movie_matches) == 1:
            return director_movie_matches[0], search_results

    # Matches por titulo
    title_matches = []
    slugify_title = clean_string(title)

    title_movie_matches = []

    for sr in clean_matches:
        if clean_string(sr['title']) == slugify_title:
            if 'kind' in sr and sr['kind'] in valid_kinds:
                # Solo si hemos encontrado con año
                if is_match_by_year:
                    imdb_movie = get_imdb_movie(sr.movieID)

                    if is_valid_imdb_movie(imdb_movie, valid_kinds=valid_kinds):
                        title_movie_matches.append(imdb_movie)
            title_matches.append(sr)

    # Si tenemos solo un match con year, titulo y es una peli valida lo damos
    # por bueno
    if len(title_movie_matches) == 1:
        return title_movie_matches[0], search_results

    # Si no hemos encontrado ningun match por titulo, buscamos en los akas
    # de los mas prometedores (esto puede tardar un wevete dependiendo
    # del numero de elementos)
    if len(title_matches) == 0 or title_alt:
        clean_titles = [slugify_title]
        if title_alt:
            clean_titles.append(clean_string(title_alt))

        for sr in clean_matches:
            # Si el titulo ya esta en title_matches pasamos al siguiente
            if match_imdb_id(sr.movieID, title_matches):
                continue
            
            for clean_title in clean_titles:
                imdb_movie = get_imdb_movie(sr.movieID)
                is_aka_match = False

                if imdb_movie and 'akas' in imdb_movie.keys():
                    for aka in imdb_movie['akas']:
                        # Quitamos el locale del aka y lo limpiamos
                        clean_aka_title = clean_string(re.sub(r'\(.*\)', '', aka))
                        if clean_aka_title == clean_title:
                            title_matches.append(sr)

                            if is_valid_imdb_movie(imdb_movie, valid_kinds=valid_kinds):
                                title_movie_matches.append(imdb_movie)
                            is_aka_match = True
                            break
                
                if is_aka_match:
                    break

    # Si tenemos solo un match con year, titulo (ahora por los akas) y 
    # es una peli valida lo damos por bueno
    if is_match_by_year and len(title_movie_matches) == 1:
        return title_movie_matches[0], search_results

    if len(title_matches) > 0:
        clean_matches = title_matches

    # Buscamos matches que sean solo de los tipos que nos interesen
    movie_matches = []
    other_matches = []

    if len(valid_kinds) > 0:
        for sr in clean_matches:
            if 'kind' in sr and sr['kind'] in valid_kinds:
                movie_matches.append(sr)
            else:
                other_matches.append(sr)
    else:
        movie_matches = clean_matches

    # Si solo hemos encontrado un movie_matches asumimos que es el bueno 
    # (si pusimos year)
    if is_match_by_year and len(movie_matches) == 1:
        imdb_movie = get_imdb_movie(movie_matches[0].movieID)

        if is_valid_imdb_movie(imdb_movie, valid_kinds=valid_kinds):
            return imdb_movie, search_results
    
    # llegados a este punto, pueden haber ocurrido varias cosas:
    #   - El titulo es muy generico y devuelve demasiados matches
    #   - Algun dato de los introducidos esta mal
    #   - La busqueda de imdb deja mucho que desear (try google.com)
    # En resumen, no sabemos como continuar asi que devolvemos
    # una lista completando con las listas que hemos sacado
    # intentando ordenar por los mas prometedores
    promisings = []

    # Ordenamos primero por los ultimos matches (movie_matches)
    for sr in movie_matches:
        promisings.append(sr)
    
    # Como segunda opcion tenemos los de director
    for sr in director_matches:
        promisings.append(sr) if not match_imdb_id(sr.movieID, promisings) else None

    # Como tercera opcion other_matches
    for sr in other_matches:
        promisings.append(sr) if not match_imdb_id(sr.movieID, promisings) else None

    # Por ultimo cogemos el resto de matches
    for sr in search_results:
        promisings.append(sr) if not match_imdb_id(sr.movieID, promisings) else None

    return None, promisings

def serialize(obj):
    return codecs.encode(pickle.dumps(obj), "base64").decode()

def unserialize(str_obj):
    return pickle.loads(codecs.decode(str_obj.encode(), "base64"))

def get_imdb_titles(imdb_movie):
    title_akas = {}
    new_titles = {}

    if 'countries' in imdb_movie.keys():
        movie_countries = imdb_movie['countries']

        trace.debug(" * Los paises de la pelicula son:")
        for c in movie_countries:
            trace.debug("      - %s" % c)

        if 'akas' in imdb_movie.keys():
            trace.debug(" * Los akas encontrados son:")
            for full_title_aka in imdb_movie['akas']:
                trace.debug("      - %s" % full_title_aka)

                # (original title)
                # World-wide (English title)
                aka_country = None
                clean_aka_title = None

                if not 'Spain' in movie_countries:
                    if full_title_aka.endswith(' Spain'):
                        aka_country = 'Spain'
                        clean_aka_title = re.sub(r' Spain$', '', full_title_aka)

                if aka_country is None:
                    for mc in movie_countries:
                        if full_title_aka.endswith(' %s' % mc):
                            aka_country = mc
                            clean_aka_title = re.sub(r' %s$' % mc, '', full_title_aka)

                if aka_country is None:
                    if full_title_aka.endswith(' (original title)'):
                        if not 'title_original' in new_titles:
                            new_titles['title_original'] = re.sub(r' \(original title\)$', '', full_title_aka)
                    elif full_title_aka.endswith(' World-wide (English title)'):
                        if not 'title' in new_titles:
                            new_titles['title'] = re.sub(r' World-wide \(English title\)$', '', full_title_aka)
                elif aka_country == 'Spain':
                    if not 'title_preferred' in new_titles:
                        new_titles['title_preferred'] = clean_aka_title

                if aka_country:
                    if not aka_country in title_akas:
                        title_akas[aka_country] = clean_aka_title
        
        if len(new_titles.keys()) == 0:
            trace.error("No conseguimos encontrar los titulos de la pelicula '%s'. [imdb_id='%s']" % (imdb_movie['title'], imdb_movie.getID()))
        else:
            if not 'title' in new_titles:
                # Que la pelicula no tenga titulo internacional no tiene porque ser un error... 
                trace.debug("La pelicula '%s' no tiene titulo internacional. [imdb_id='%s']" % (imdb_movie['title'], imdb_movie.getID()))
                new_titles['title'] = imdb_movie['title']
                """
                if 'title_original' in new_titles:
                    new_titles['title'] = new_titles['title_original']
                else:
                    new_titles['title'] = new_titles['title_preferred']
                """

            if not 'title_original' in new_titles:
                trace.error("La pelicula '%s' no tiene titulo original. [imdb_id='%s']" % (imdb_movie['title'], imdb_movie.getID()))
                if 'title' in new_titles:
                    new_titles['title_original'] = new_titles['title']
                else:
                    new_titles['title_original'] = new_titles['title_preferred']
                
            if not 'title_preferred' in new_titles:
                # Puede que se trate de una peli que el titulo original ya esta en 
                # spanish, por eso no te aparece en el aka
                is_spanish_movie = False
                for c in imdb_movie['countries']:
                    if c == 'Spain' or c == 'Argentina':
                        is_spanish_movie = True

                if not is_spanish_movie:
                    # Que la peli no tenga titulo en español no tiene porque ser un error
                    # muchas no lo tienen, aunque es un buen indicativo de que la peli
                    # puede estar mal capturada... (sobre todo si se trata de una peli
                    # popular)
                    trace.debug("La pelicula '%s' no tiene titulo en español. [imdb_id='%s']" % (imdb_movie['title'], imdb_movie.getID()))
                
                if 'title' in new_titles:
                    new_titles['title_preferred'] = new_titles['title']
                else:
                    new_titles['title_preferred'] = new_titles['title_original']
    else:
        trace.error("La pelicula '%s' no tiene pais. [imdb_id='%s']" % (imdb_movie['title'], imdb_movie.getID()))

    return new_titles, title_akas

def get_imdb_movie(imdb_id):
    if not NO_CACHE:
        cache_data = IMDB_CACHE_OBJS.filter(imdb_id=imdb_id).all()

        if cache_data.count() > 0:
            if not UPDATE_CACHE:
                return unserialize(cache_data[0].raw_data)
            else:
                IMDB_CACHE_OBJS.filter(imdb_id=imdb_id).delete()
    
    imdb_movie = IMDB_API.get_movie(imdb_id, ('main', 'plot', 'akas'))

    if not NO_CACHE or UPDATE_CACHE:
        IMDB_CACHE_OBJS.create(
            imdb_id=imdb_id,
            raw_data=serialize(imdb_movie)
        )

    return imdb_movie

def search_imdb_movies(search_query, title=None, year=None):
    if not NO_CACHE:
        cache_data = IMDB_CACHE_OBJS.filter(search_query=search_query).all()

        if cache_data.count() > 0:
            if not UPDATE_CACHE:
                return unserialize(cache_data[0].raw_data)
            else:
                IMDB_CACHE_OBJS.filter(search_query=search_query).delete()
    
    imdb_results = IMDB_API.search_movie(search_query, results=5)

    for sr in imdb_results:
        if not 'year' in sr or not sr['year']:
            trace.debug('\t\t\t\t* Año no existente en los resultados. Obteniendo detalle de %s' % sr.movieID)
            imdb_movie = get_imdb_movie(sr.movieID)
            if not imdb_movie is None and 'year' in imdb_movie.keys():
                sr['year'] = imdb_movie['year']
                if not year is None and str(year) == str(imdb_movie['year']) and not title is None and title == imdb_movie['title']:
                    break
    
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
    def imdb_data(movie, storage_match=False):
        facade_result = FacadeResult()
        facade_result.is_local_data = False
        facade_result.storage_match = storage_match
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
        return FacadeResult.imdb_data(get_imdb_movie(imdb_id))

def facade_search(title, year, title_alt=None, director=None, storage_type=None, 
    storage_name=None, path=None, imdb_id=None, not_an_imdb_movie=False):
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
    imdb_movie, search_results = match_imdb_movie(
        title, year, title_alt=title_alt, 
        director=director
    )

    if not imdb_movie is None:
        # Por ultima vez comprobamos que no la tenemos dada de alta en local
        local_movies = Movie.objects.filter(imdb_id=imdb_movie.getID()).all()

        if local_movies.count() == 0:
            return FacadeResult.imdb_data(imdb_movie)

        return FacadeResult.local_data(local_movies[0])
    
    if search_results is None or len(search_results) == 0:
        return None
    

    # Llegados a este punto no hemos encontrado ninguna coincidencia decente
    # sacamos un mensaje y devolvemos None
    trace.debug(" * No encontramos coincidencia clara para la peli '%s (%s)' *" % (title, year))
    trace.debug(" * Aunque hemos encontrado las siguientes: *")
    trace_results(search_results, mini_info=True)

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

def match_imdb_movie_by_director(search_results, director):
    matches = []

    for sr in search_results:
        movie = get_imdb_movie(sr.movieID)
        if 'director' in movie.keys():
            # Con que coincida un director damos la pelicula como buena
            if match_director(director, movie['director']):
                matches.append(sr)
    
    # Llegados a este punto no hemos encontrado ninguna coincidencia decente
    # asi que lo damos por perdido
    return matches

def match_director(director, imdb_directors):
    movie_directors = [clean_string(p['name']) for p in imdb_directors]

    for p in imdb_directors:
        if 'canonical name' in p and p['canonical name']:
            movie_directors.append(clean_string(p['canonical name']))
        elif 'canonica_name' in p and p['canonica_name']:
            movie_directors.append(clean_string(p['canonica_name']))
    
    directors = slugify_directors(director)

    for slugify_director in directors:
        if slugify_director in movie_directors:
            return True
    
    trace.debug("SLUGIFY INPUT DIRECTORS:")
    trace.debug(directors)
    trace.debug("SLUGIFY IMDB DIRECTORS:")
    trace.debug(movie_directors)

    return False

def is_valid_imdb_movie(imdb_movie, valid_kinds=IMDB_VALID_MOVIE_KINDS):
    if not 'kind' in imdb_movie.keys():
        return False
    elif not imdb_movie['kind'] in valid_kinds:
        return False
    
    if not 'full-size cover url' in imdb_movie.keys() or not imdb_movie['full-size cover url']:
        return False
    
    return True

def trace_results(search_results, mini_info=False):
    if trace.is_debug():
        for sr in search_results:
            trace.debug("  - %s (%s) [%s] https://www.imdb.com/title/tt%s" % (sr['title'], sr['year'] if 'year' in sr and sr['year'] else 'None', sr.movieID, sr.movieID))
            if not mini_info:
                movie = get_imdb_movie(sr.movieID)
                if 'director' in movie.keys():
                    trace.debug("      DIRECTORES:")
                    movie_directors = [clean_string(p['name']) for p in movie['director']]
                    for director in movie_directors:
                        trace.debug("        * '%s'" % director)
                trace.debug("      TIPO DE PELICULA: '%s'" % sr['kind'] if 'kind' in sr and sr['kind'] else '')
                trace.debug("      PORTADA: '%s'" % movie['full-size cover url'] if 'full-size cover url' in movie.keys() and movie['full-size cover url'] else '')

            # kitty console:
            # show_imdb_movie_image(movie)

def search_movie_imdb(title, year=None, title_alt=None, director=None):
    search_results = None
    clean_title = clean_string(title)

    if title and year:
        # Buscamos por titulo y año en IMDB
        trace.debug('\t\t\t- Buscando en imdb por titulo y año "title=%s year=%s"...' % (title, year))
        search_results = search_imdb_movies('%s (%s)' % (title, year), title=title, year=year)

        if search_results is None or len(search_results) == 0:
            trace.debug('\t\t\t- Buscando en imdb por titulo limpio y año "clean_title=%s year=%s"...' % (clean_title, year))
            search_results = search_imdb_movies('%s (%s)' % (clean_title, year), title=clean_title, year=year)
    
    if search_results is None or len(search_results) == 0:
        trace.debug('\t\t\t- Buscando en imdb por titulo "title=%s"...' % title)
        search_results = search_imdb_movies(title, title=title)
    
    if search_results is None or len(search_results) == 0:
        trace.debug('\t\t\t- Buscando en imdb por titulo limpio "clean_string(title)=%s"...' % clean_string(title))
        search_results = search_imdb_movies(clean_title, title=clean_title)
    
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
