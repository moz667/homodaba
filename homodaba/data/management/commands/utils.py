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