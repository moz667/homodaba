from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.utils.translation import gettext as _
from django.utils.text import slugify

from data.models import Movie, Person, MovieStorageType, MoviePerson, Tag, GenreTag, TitleAka, ContentRatingTag
from data.models import get_first_or_create_tag, populate_movie_auto_tags

from data.utils import Trace as trace
from data.utils.imdbpy_facade import facade_search, get_imdb_titles

import csv
from datetime import datetime
import sys

from .utils import trace_validate_imdb_movie, normalize_age_certificate, clean_csv_data, csv_validate

HELP_TEXT = """
Descripcion de los campos del csv:

OBLIGATORIOS:
    title: Titulo de la pelicula (OBLIGATORIO)

    year: Año de estreno (OBLIGATORIO)

OPCIONALES:
    imdb_id: Identificador de imdb para forzar la busqueda de esa peli (por defecto: 
        None) (opcional)

    storage_name: identificador del almacenamiento (nombre del disco duro, 
        carpeta compartida...) (opcional, aunque hay que tener en cuenta
        que si no se define, ó es 'Original', tomara que el medio es 
        original)

    media_format: Formato en el que esta almacenado el medio (ver 
        models.MovieStorageType.MEDIA_FORMATS para mas info de los 
        disponibles) (opcional, por defecto DVD)

    storage_type: Tipo de almacenamiento en el se encuentra el medio 
        (ver models.MovieStorageType.STORAGE_TYPES para mas info de los 
        disponibles) (opcional, por defecto DVD)

    path_no_extension: Campo especial para definir donde se almacena el 
        medio SIN EXTENSION de archivo (en caso de discos duros, carpetas 
        compartidas...) (opcional)

    path: Ruta completa (con extension si fuera necesaria) al medio
        (opcional, hay que tener en cuenta que si path no tiene valor, pero
        por el contrario hemos incluido el campo path_no_extension, 
        intentara averiguar el valor de path en base a path_no_extension y
        media_format, por ejemplo para estos valores:
        media_format=AVI
        path_no_extension=carpeta/fichero_sin_extension
        path se calculara como:
        path=carpeta/fichero_sin_extension.avi)

    title_preferred: Titulo en el idioma materno del usuario (por defecto: 
        Español) (opcional)

    director: Director de la pelicula (directores separados por coma) 
        (opcional y no muy necesario ya que esa info nos la da 
        alegremente imdb)

    resolution: Resolución del medio (1080p, 2060p... etc) (opcional)
    
    tags: Etiquetas separadas por coma, lo usamos para identificar sagas (optional)
    
    title_original: Titulo original de la película, si se suministra ignora
        el de imdb que parece que siempre lo devuelve en ingles.

    version: Version de la película, (Director's cut, Theatrical's cut...) (opcional)
"""

class Command(BaseCommand):
    help = _('Importa datos desde un CSV')

    """
    Pinta la ayuda y sale
    """
    def csv_file_help(self):
        print(HELP_TEXT)
        exit()

    """
    Argumentos del comando:

    """
    def add_arguments(self, parser):
        parser.add_argument('--csv-file', nargs='+', type=str, help="""Fichero csv con los datos a importar.""")
        parser.add_argument('--from-title', nargs='+', type=str, help="""Empieza a tratar desde la fila que se titule igual que el valor de este parametro.""")
        parser.add_argument(
            '--csv-file-help',
            action='store_true',
            help='Ayuda ampliada acerca del archivo csv.',
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


    def get_or_create_person(self, ia_person):
        local_persons = Person.objects.filter(imdb_id=ia_person.getID()).all()

        if local_persons.count() > 0:
            return local_persons[0]
        
        return Person.objects.create(
            name=ia_person['name'],
            canonical_name=ia_person['canonical name'],
            imdb_id=ia_person.getID(),
        )

    def get_or_insert_movie(self, r):
        trace.debug('Tratando "%s (%s)"...' % (r['title'], r['year']))
        
        cd = clean_csv_data(r)

        facade_result = facade_search(
            title=cd['title'], year=r['year'], 
            title_alt=cd['title_alt'],
            director=cd['director'],
            storage_type=cd['storage_type'],
            storage_name=cd['storage_name'],
            path=cd['path'],
            imdb_id=cd['imdb_id'],
        )

        tags = r['tags'].split(',') if 'tags' in r and r['tags'] else []

        if not facade_result:
            trace.error('\tParece que no encontramos la pelicula "%s (%s)"' % (cd['title'], r['year']))
            return None

        if facade_result.is_local_data:
            # 1.1) si la esta, sacamos un mensaje y devolvemos la pelicula (FIN)
            trace.warning("\tYa tenemos una película con el título '%s' del año '%s'" % (cd['title'], r['year']))

            # Solo insertamos storage si no fue una coincidencia de storage
            if not facade_result.storage_match:
                self.get_or_insert_storage(
                    movie=facade_result.movie, 
                    is_original=cd['is_original'], 
                    storage_type=cd['storage_type'], 
                    storage_name=cd['storage_name'], 
                    path=cd['path'], 
                    resolution=cd['resolution'], 
                    media_format=cd['media_format'], 
                    version=cd['version'], 
                )

                # Puede ocurrir, cuando se trata de un nuevo storage, que lleve nuevas 
                # tags (por ejemplo, una version extendida de una peli, 3D...)
                if len(tags):
                    tagged = False

                    for tag in tags:
                        db_tag = get_first_or_create_tag(
                            Tag, name=tag
                        )

                        if not db_tag in facade_result.movie.tags.all():
                            tagged = True
                            facade_result.movie.tags.add(db_tag)
                    
                    if tagged:
                        facade_result.movie.save()

                populate_movie_auto_tags(facade_result.movie)
            return facade_result.movie
       
        trace_validate_imdb_movie(facade_result.movie, cd['title'], director=cd['director'])

        local_movie = self.insert_movie(
            r['title'],
            facade_result.movie, 
            tags=tags,
            title_original=r['title_original'] if 'title_original' in r and r['title_original'] else None,
            title_preferred=r['title_preferred'] if 'title_preferred' in r and r['title_preferred'] else None,
        )

        self.get_or_insert_storage(
            movie=local_movie, 
            is_original=cd['is_original'], 
            storage_type=cd['storage_type'], 
            storage_name=cd['storage_name'], 
            path=cd['path'], 
            resolution=cd['resolution'], 
            media_format=cd['media_format'], 
            version=cd['version'], 
        )

        # 2.6) Devolvemos la pelicula
        return local_movie

    def get_or_insert_storage(self, movie, is_original=True, storage_type=None, storage_name=None, path=None, resolution=None, media_format=None, version=None):
        # Comprobamos que la relacion entre pelicula y tipo de almacenamiento no exista ya
        storages = MovieStorageType.objects.filter(
            movie=movie, 
            is_original=is_original, 
            storage_type=storage_type, 
            name=storage_name,
            path=path,
            media_format=media_format,
            resolution=resolution,
            version=version
        )

        # de ser asi sacar mensaje notificandolo
        if storages.count() > 0:
            trace.warning('\tYa tenemos la pelicula "%s" del año "%s" dada de alta con esos datos de almacenamiento!' % (movie.title, movie.year))
            return storages[0]
        
        # 2.5) Damos de alta la relacion entre pelicula y tipo de almacemaniento (MovieStorageType)
        MovieStorageType.objects.create(
            movie=movie, 
            is_original=is_original, 
            storage_type=storage_type, 
            name=storage_name,
            path=path,
            media_format=media_format,
            resolution=resolution,
            version=version,
        )

    def insert_movie(self, title, ia_movie, tags=[], title_original=None, title_preferred=None):
        # 2.2.4) Para cada uno de los directores
        directors = []

        if 'director' in ia_movie.keys():
            for ia_person in ia_movie['director']:
                # 2.2.4.1) Buscamos si lo tenemos dado de alta (imdb_id)
                # 2.2.4.1.1) Si lo tenemos dado de alta lo recuperamos de la bbdd
                # 2.2.4.1.2) Si no, lo damos de alta las personas implicadas con los datos basicos (sin recuperar detalle)
                lp = self.get_or_create_person(ia_person)

                if not lp.is_director:
                    lp.is_director = True
                    lp.save()
                
                directors.append(lp)
        else:
            trace.warning('\tinsert_movie: No encontramos directores para la pelicula "%s"' % title)
        
        # 2.2.5) Para cada uno de los escritores (lo mismo que para directores)
        writers = []

        if 'writer' in ia_movie.keys():
            for ia_person in ia_movie['writer']:
                lp = self.get_or_create_person(ia_person)

                if not lp.is_writer:
                    lp.is_writer = True
                    lp.save()
                
                writers.append(lp)
        else:
            trace.warning('\tNo encontramos escritores para la pelicula "%s"' % title)
        
        # 2.2.5) Para cada uno de casting (lo mismo que para directores)
        casting = []

        if 'cast' in ia_movie.keys():
            for ia_person in ia_movie['cast']:
                lp = self.get_or_create_person(ia_person)

                if not lp.is_actor:
                    lp.is_actor = True
                    lp.save()
                
                casting.append(lp)
        else:
            trace.warning('\tNo encontramos casting para la pelicula "%s"' % title)
        
        new_titles, title_akas = get_imdb_titles(ia_movie)
        
        if not title_original and 'title_original' in new_titles and new_titles['title_original']:
            title_original = new_titles['title_original']

        if not title_preferred and 'title_preferred' in new_titles and new_titles['title_preferred']:
            title_preferred = new_titles['title_preferred']

        # TODO: Que hacemos aqui... ponemos el titulo del csv o el de ia_movie?
        local_movie = Movie.objects.create(
            title=new_titles['title'] if 'title' in new_titles and new_titles['title'] else title,
            title_original=title_original,
            title_preferred=title_preferred,
            imdb_id=ia_movie.getID(),
            kind=ia_movie['kind'],
            summary=ia_movie.summary(),
            poster_url=ia_movie['full-size cover url'] if 'full-size cover url' in ia_movie.keys() else None,
            poster_thumbnail_url=ia_movie['cover url'] if 'cover url' in ia_movie.keys() else None,
            year=ia_movie['year'],
            rating=ia_movie['rating'] if 'rating' in ia_movie.keys() else None,
            imdb_raw_data=ia_movie.asXML(),
        )

        tagged = False

        if len(title_akas.keys()) > 0:
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
                
                local_movie.title_akas.add(db_title_aka)
            
        if 'genres' in ia_movie.keys():
            tagged = True

            for tag in ia_movie['genres']:
                local_movie.genres.add(
                    get_first_or_create_tag(
                        GenreTag, name=tag
                    )
                )

        if 'certificates' in ia_movie.keys():
            valid_certs = []
            if len(ia_movie['certificates']) > 0:
                for c in ia_movie['certificates']:
                    if c and c.startswith('United States:'):
                        valid_cert = c.replace('United States:', '')
                        if not valid_cert in valid_certs:
                            valid_certs.append(valid_cert)

            if len(valid_certs) > 0:
                tagged = True
                for vc in valid_certs:
                    vc_tag = get_first_or_create_tag(
                        ContentRatingTag, name=normalize_age_certificate(vc)
                    )

                    if not vc_tag in local_movie.content_rating_systems.all():
                        local_movie.content_rating_systems.add(vc_tag)
            else:
                trace.warning('No se encontraron clasificaciones de edad para "%s"' % local_movie.get_complete_title())

        if len(tags):
            tagged = True

            for tag in tags:
                local_movie.tags.add(
                    get_first_or_create_tag(
                        Tag, name=tag
                    )
                )

        if tagged:
            local_movie.save()

        populate_movie_auto_tags(local_movie)

        # 2.4) Damos de alta las relaciones entre peliculas y personas de todas las recuperadas antes (directores, escritores, casting...)
        for d in directors:
            MoviePerson.objects.create(
                movie=local_movie,
                person=d,
                role=MoviePerson.RT_DIRECTOR
            )
            # Tambien lo damos de alta en el m2m de directors:
            local_movie.directors.add(d)
        
        if len(directors) > 0:
            # Tenemos que guardar si habia directors:
            local_movie.save()

        for w in writers:
            MoviePerson.objects.create(
                movie=local_movie,
                person=w,
                role=MoviePerson.RT_WRITER
            )

        for c in casting:
            MoviePerson.objects.create(
                movie=local_movie,
                person=c,
                role=MoviePerson.RT_ACTOR
            )

        return local_movie

    def handle(self, *args, **options):
        if options['csv_file_help']:
            self.csv_file_help()
        
        if not 'csv_file' in options or not options['csv_file'] or not options['csv_file'][0]:
            self.print_help('manage.py', __name__)
            return

        csv_delimiter = ';'
        if 'delimiter' in options and options['delimiter'] and options['delimiter'][0]:
            csv_delimiter = options['delimiter'][0]

        csv_quotechar = '|'
        if 'quotechar' in options and options['quotechar'] and options['quotechar'][0]:
            csv_quotechar = options['quotechar'][0]

        from_title = options['from_title'] if 'from_title' in options and options['from_title'] and len(options['from_title']) > 0 else None
        from_title = ' '.join(from_title) if from_title else None

        verbosity = options['verbosity']
        trace.set_verbosity(verbosity)

        fieldnames = []

        with open(options['csv_file'][0], newline='') as csvfile:
            csv_reader = csv.DictReader(csvfile, delimiter=csv_delimiter, quotechar=csv_quotechar)
            fieldnames = csv_reader.fieldnames
            for r in csv_reader:
                csv_validate(r)
        
        now = datetime.now()

        csv_fails = open('fail-%s.csv' % now.strftime('%Y%m%d-%H%M%S'), 'w', newline='')
        csv_done = open('done-%s.csv' % now.strftime('%Y%m%d-%H%M%S'), 'w', newline='')
        csv_writer_fails = csv.DictWriter(csv_fails, fieldnames=fieldnames, delimiter=csv_delimiter, quotechar=csv_quotechar)
        csv_writer_done = csv.DictWriter(csv_done, fieldnames=fieldnames, delimiter=csv_delimiter, quotechar=csv_quotechar)
        csv_writer_fails.writeheader()
        csv_writer_done.writeheader()

        with open(options['csv_file'][0], newline='') as csvfile:
            csv_reader = csv.DictReader(csvfile, delimiter=csv_delimiter, quotechar=csv_quotechar)
            
            start = not from_title

            for csv_row in csv_reader:
                if from_title and from_title == csv_row['title']:
                    start = True
                
                if start:
                    try:
                        cur_movie = self.get_or_insert_movie(csv_row)
                        if cur_movie is None:
                            csv_writer_fails.writerow(csv_row)
                        else:
                            csv_writer_done.writerow(csv_row)
                    except:
                        trace.error("Error no esperado", sys.exc_info()[0])
                        csv_writer_fails.writerow(csv_row)
                        raise

                    trace.debug("")
