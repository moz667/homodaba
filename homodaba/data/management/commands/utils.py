from data.models import Movie, MovieStorageType

from data.utils.imdbpy_facade import clean_string, match_director
from data.utils import Trace as trace

import json
import re

def strtobool(val):
    val = val.lower()
    if val in ('y', 'yes', 't', 'true', 'on', '1'):
        return True
    elif val in ('n', 'no', 'f', 'false', 'off', '0'):
        return False
    else:
        raise ValueError(f"Valor no válido: {val}")

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
    year = int(r['year']) if 'year' in r and r['year'] else Movie.DEFAULT_NO_YEAR
    is_original = True if not storage_name else False
    imdb_id = r['imdb_id'] if 'imdb_id' in r and r['imdb_id'] else None

    not_an_imdb_movie = False
    if 'not_an_imdb_movie' in r:
        if isinstance(r['not_an_imdb_movie'], str) and r['not_an_imdb_movie']:
            not_an_imdb_movie = strtobool(r['not_an_imdb_movie'])
        elif r['not_an_imdb_movie']:
            not_an_imdb_movie = True

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
Compara los datos recuperados de la API en facade_movie con el title y director que 
le pasamos como parametro.
Si no coinciden, sacamos un mensaje notificando las diferencias.
"""
def trace_validate_facade_movie(facade_movie, title, director=None):
    # Puede que el titulo de la pelicula este mal en el CSV, asi que lo notificamos:
    if clean_string(facade_movie.title) != clean_string(title):
        trace.info('\tEl titulo de la pelicula "%s" no corresponde con el cargado del imdb "%s"' % (title, facade_movie.title))

    # 2.2.3) Si r tiene directores, los validamos, si no son los mismos, sacamos mensaje
    if director:
        if len(facade_movie.directors) == 0:
            trace.info('\trace_validate_facade_movie: No encontramos directores para la pelicula "%s"' % facade_movie.title)
        else:
            if not match_director(director, facade_movie.directors):
                # Esto es para que revises tu csv!!!
                trace.info("\tNo encontramos el/los director/es '%s' en IMDB para la pelicula '%s'" % (director, title))

