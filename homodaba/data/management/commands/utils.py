from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.utils.translation import gettext as _
from django.utils.text import slugify

from data.models import Movie, Person, MovieStorageType, MoviePerson, Tag, GenreTag, TitleAka, ContentRatingTag
from data.models import get_first_or_create_tag

from data.utils.imdbpy_facade import clean_string, match_director
from data.utils import Trace as trace

from imdb import IMDb

import csv
from datetime import datetime
from distutils.util import strtobool
import json
import re
import sys
from time import sleep

"""
Divide un nombre de archivo (sin ruta) en partes diferenciadas
{
    'ext', extension
    'name', nombre sin la extension ni el punto
    'fullname', el nombre que le pasamos como parametro
}
"""
def split_filename_parts(filename):
    parts = filename.split('.')

    # Si tiene extension:
    if len(parts) > 1:
        extension_index = (len(parts) - 1)

        return {
            'ext': parts[extension_index],
            'name': '.'.join(parts[:extension_index]),
            'fullname': filename
        }
    
    # Si no tiene extension
    return {
        'fullname': filename
    }

"""
Guarda un obj en un json formateandolo bonito
"""
def save_json(obj, filename):
    dump_file = open(filename, 'w', newline='')
    dump_file.write(json.dumps(obj, indent=4, sort_keys=True, ensure_ascii=False))

"""
Divide una lista en 2 listas 
"""
def divide_list_on_two(full_list):
    # Si tiene solo un elemento, devolvemos la lista y una vacia
    if len(full_list) == 1:
        return full_list, []
    
    middle_index = int(len(full_list) / 2)
    
    first_half = full_list[:middle_index]
    second_half = full_list[middle_index:]

    return first_half, second_half

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
    title_original = r['title_original'] if 'title_original' in r else None
    title_preferred = r['title_preferred'] if 'title_preferred' in r else None
    title_alt = title_preferred if title_preferred else title_original

    storage_name = r['storage_name'] if 'storage_name' in r and r['storage_name'] and r['storage_name'] != 'Original' else None
    director = r['director'] if 'director' in r and r['director'] else None
    year = r['year'] if 'year' in r and r['year'] else 1800
    is_original = True if not storage_name else False
    imdb_id = r['imdb_id'] if 'imdb_id' in r and r['imdb_id'] else None

    not_an_imdb_movie = strtobool(r['not_an_imdb_movie']) if 'not_an_imdb_movie' and r['not_an_imdb_movie'] else False

    tags = r['tags'].split(',') if 'tags' in r and r['tags'] else []
    directors = director.split(",") if director else []

    storage_type = MovieStorageType.ST_DVD
    if 'storage_type' in r and r['storage_type']:
        if not r['storage_type'] in MovieStorageType.STORAGE_TYPES_AS_LIST:
            trace.warning('\tstorage_type "%s" no encontrado en la lista de soportados.' % r['storage_type'])
        else:
            storage_type = r['storage_type']
    
    media_format = MovieStorageType.MF_DVD
    if 'media_format' in r and r['media_format']:
        if not r['media_format'] in MovieStorageType.MEDIA_FORMATS_AS_LIST:
            trace.warning('\tmedia_format "%s" no encontrado en la lista de soportados.' % r['media_format'])
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
        'title_original':title_original,
        'title_preferred':title_preferred,
        'title_alt':title_alt,
        'storage_name':storage_name,
        'director':director,
        'year':year,
        'is_original':is_original,
        'imdb_id':imdb_id,
        'not_an_imdb_movie':not_an_imdb_movie,
        'storage_type':storage_type,
        'media_format':media_format,
        'path':path,
        'version':version,
        'resolution':resolution,
        'tags': tags,
        'directors': directors,
    }

def normalize_age_certificate(raw_certificate):
    if '::' in raw_certificate:
        return re.compile('::.*').sub('', raw_certificate)
    
    return raw_certificate

"""
Compara los datos recuperados de imdb en ia_movie con el title y director que 
le pasamos como parametro.
Si no coinciden, sacamos un mensaje notificando las diferencias.
"""
def trace_validate_imdb_movie(ia_movie, title, director=None):
    # Puede que el titulo de la pelicula este mal en el CSV, asi que lo notificamos:
    if clean_string(ia_movie['title']) != clean_string(title):
        trace.info('\tEl titulo de la pelicula "%s" no corresponde con el cargado del imdb "%s"' % (title, ia_movie['title']))

    # 2.2.3) Si r tiene directores, los validamos, si no son los mismos, sacamos mensaje
    if director:
        if not 'director' in ia_movie.keys():
            trace.info('\ttrace_validate_ia_movie: No encontramos directores para la pelicula "%s"' % ia_movie['title'])
        else:
            if not match_director(director, ia_movie['director']):
                # Esto es para que revises tu csv!!!
                trace.info("\tNo encontramos el/los director/es '%s' en IMDB para la pelicula '%s'" % (director, title))


"""
Busqueda interactiva.

TODO: No se esta usando pero lo dejamos por aqui por si queremos retomarlo
TODO: Si lo volvemos a usar, utilizar la cache
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
                trace.error("\tParece que NO encontramos películas con el título '%s' del año '%s'" % (title, year))
                exit()
            elif input_return == 'n':
                trace.error("\tParece que NO encontramos películas con el título '%s' del año '%s'" % (title, year))
                return None
            else:
                try:
                    input_return = int(input_return)
                    if not (input_return > 0 and input_return <= len(search_results)):
                        trace.error("\tEse valor no es posible.")
                        input_return = ""
                except ValueError:
                    trace.error("\tEse valor no es posible.")
                    input_return = ""
        
        return search_results[int(input_return) - 1]
    
    # No encontramos ni una...
    return None
"""