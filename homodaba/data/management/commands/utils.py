from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.utils.translation import gettext as _
from django.utils.text import slugify

from data.models import Movie, Person, MovieStorageType, MoviePerson, Tag, GenreTag, TitleAka, ContentRatingTag
from data.models import get_first_or_create_tag

from data.utils.imdbpy_facade import facade_search

from imdb import IMDb

import csv
from datetime import datetime
import re
import sys
from time import sleep

def csv_validate(r):
    if not 'title' in r or not r['title']:
        raise Exception("ERROR!: El titulo es obligatorio y tiene que estar definido en el CSV como 'title'.")
    if not 'year' in r or not r['year']:
        raise Exception("ERROR!: El año de estreno es obligatorio y tiene que estar definido en el CSV como 'year'.")


def clean_csv_data(r):
    """
    Tenemos que averiguar primero:
    1) Si se trata de una peli original
    2) El archivo donde se almacena si no lo es
    """
    title = r['title']
    title_alt = r['title_preferred'] if 'title_preferred' in r and r['title_preferred'] else None
    storage_name = r['storage_name'] if 'storage_name' in r and r['storage_name'] and r['storage_name'] != 'Original' else None
    director = r['director'] if 'director' in r and r['director'] else None
    is_original = True if not storage_name else False
    imdb_id = r['imdb_id'] if 'imdb_id' in r and r['imdb_id'] else None

    storage_type = MovieStorageType.ST_DVD
    if 'storage_type' in r and r['storage_type']:
        if not r['storage_type'] in MovieStorageType.STORAGE_TYPES_AS_LIST:
            print('\tWARNING! storage_type "%s" no encontrado en la lista de soportados.' % r['storage_type'])
        else:
            storage_type = r['storage_type']
    
    media_format = MovieStorageType.MF_DVD
    if 'media_format' in r and r['media_format']:
        if not r['media_format'] in MovieStorageType.MEDIA_FORMATS_AS_LIST:
            print('\tWARNING! media_format "%s" no encontrado en la lista de soportados.' % r['media_format'])
        else:
            media_format = r['media_format']

    path = r['path'] if not is_original and 'path' in r and r['path'] else None

    if not is_original and not path and 'path_no_extension' in r and r['path_no_extension']:
        path = r['path_no_extension']
        if media_format:
            if media_format in MovieStorageType.MEDIA_FORMATS_FILE_WITH_ISO_EXTENSION:
                path = path + ".iso"
            elif media_format in MovieStorageType.MEDIA_FORMATS_FILE_WITH_OTHER_EXTENSION:
                path = path + ".%s" % media_format.lower()
    
    version = r['version'] if 'version' in r and r['version'] else None
    resolution = r['resolution'] if 'resolution' in r and r['resolution'] else None

    return {
        'title':title,
        'title_alt':title_alt,
        'storage_name':storage_name,
        'director':director,
        'is_original':is_original,
        'imdb_id':imdb_id,
        'storage_type':storage_type,
        'media_format':media_format,
        'path':path,
        'version':version,
        'resolution':resolution,
    }

def normalize_age_certificate(raw_certificate):
    if '::' in raw_certificate:
        return re.compile('::.*').sub('', raw_certificate)
    
    return raw_certificate

"""
Por chorra que pueda parecer, recuperar el titulo original de una peli
es dificil (al menos con esta api de imdb).
hay un campo que es ia_movie['original title'], pero no suele venir con 
el titulo original, viene mas con el titulo del entorno de la api (que 
npi cual es, esto deberiamos investigarlo un poco... :P)

TODO: Investigar en que entorno se ejecuta la API (idioma, pais?)
"""
def get_imdb_original_title(ia_movie):
    if 'countries' in ia_movie.keys() and 'akas' in ia_movie.keys():
        for country in ia_movie['countries']:
            for aka in ia_movie['akas']:
                if aka.endswith('(%s)' % country):
                    return aka.replace('(%s)' % country, '').strip()
    
    # TODO: Comentar con perico... el problema es que casi nunca viene bien...
    # return ia_movie['original title']
    return None

"""
Compara los datos recuperados de imdb en ia_movie con el title y director que 
le pasamos como parametro.
Si no coinciden, sacamos un mensaje notificando las diferencias.
"""
def trace_validate_imdb_movie(ia_movie, title, director=None):
    # Puede que el titulo de la pelicula este mal en el CSV, asi que lo notificamos:
    if ia_movie['title'] != title:
        print('\tINFO: El titulo de la pelicula "%s" no corresponde con el cargado del imdb "%s"' % (title, ia_movie['title']))

    # 2.2.3) Si r tiene directores, los validamos, si no son los mismos, sacamos mensaje
    if director:
        if not 'director' in ia_movie.keys():
            print('\tINFO: trace_validate_ia_movie: No encontramos directores para la pelicula "%s"' % ia_movie['title'])
        else:
            ia_directors = [p['name'] for p in ia_movie['director']]

            for director_name in director.split(','):
                if not director_name in ia_directors:
                    # Esto es para que revises tu csv!!!
                    print("\tINFO: No encontramos el director '%s' en IMDB para la pelicula '%s'" % (director_name, title))


"""
Busqueda interactiva.

TODO: No se esta usando pero lo dejamos por aqui por si queremos retomarlo
TODO: Si lo volvemos a usar, utilizar la cache
"""
def interactive_imdb_search(title, year, title_alt=None):
    ia = IMDb(reraiseExceptions=True)
    search_results = ia.search_movie('%s (%s)' % (title, year))
            
    if len(search_results) == 0:
        search_results = ia.search_movie(title)
    
    if len(search_results) == 0 and title_alt:
        return interactive_imdb_search(title_alt, year)

    if len(search_results) > 0:
        print('\tParece que no encontramos la pelicula "%s (%s)" ¿Es alguna de estas?:' % (title, year))
        i = 1
        for sr in search_results:
            print("\t%s) %s (%s)" % (str(i), sr['title'], sr['year']))
            i = i + 1
        print("\tn) Para continuar con el siguiente")
        print("\tq) Para salir")

        input_return = ''
        while not input_return:
            input_return = input("")

            if input_return == 'q':
                print("\tERROR!: Parece que NO encontramos películas con el título '%s' del año '%s'" % (title, year))
                exit()
            elif input_return == 'n':
                print("\tERROR!: Parece que NO encontramos películas con el título '%s' del año '%s'" % (title, year))
                return None
            else:
                try:
                    input_return = int(input_return)
                    if not (input_return > 0 and input_return <= len(search_results)):
                        print("\tERROR!: Ese valor no es posible.")
                        input_return = ""
                except ValueError:
                    print("\tERROR!: Ese valor no es posible.")
                    input_return = ""
        
        return search_results[int(input_return) - 1]
    
    # No encontramos ni una...
    return None