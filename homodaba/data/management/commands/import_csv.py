from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.utils.translation import gettext as _
from django.utils.text import slugify

from data.models import Movie, Person, MovieStorageType, MoviePerson, Tag, GenreTag, TitleAka
from data.models import get_first_or_create_tag

from imdb import IMDb

import csv
from datetime import datetime
import sys
from time import sleep

SLEEP_DELAY = 0

class Command(BaseCommand):
    help = _('Importa datos desde un CSV')

    def csv_file_help(self):
        # TODO: Si te lo quieres currar mas bpk... be my guest ;D
        print("""
Descripcion de los campos del csv:

OBLIGATORIOS:
    title: Titulo de la pelicula (OBLIGATORIO)

    year: Año de estreno (OBLIGATORIO)

OPCIONALES:
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
    """)
        exit()

    def validate(self, r):
        if not 'title' in r or not r['title']:
            raise Exception("ERROR!: El titulo es obligatorio y tiene que estar definido en el CSV como 'title'.")
        if not 'year' in r or not r['year']:
            raise Exception("ERROR!: El año de estreno es obligatorio y tiene que estar definido en el CSV como 'year'.")

    def add_arguments(self, parser):
        parser.add_argument('--csv-file', nargs='+', type=str, help="""Fichero csv con los datos a importar.""")
        parser.add_argument('--from-title', nargs='+', type=str, help="""Empieza a tratar desde la fila que se titule igual que el valor de este parametro.""")
        parser.add_argument('--imdba-delay', nargs='+', type=int, help="""Retardo entre llamadas al imdb (util si te da muchos errores de conexion).""")
        parser.add_argument(
            '--csv-file-help',
            action='store_true',
            help='Ayuda ampliada acerca del archivo csv.',
        )
        parser.add_argument(
            '--interactive',
            action='store_true',
            help='Requiere interactuar cuando encuentre un problema, en cualquier otro caso saca informacion acerca del mismo.',
        )
        # delimiter=';', quotechar
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


    def search_movie_local_data(self, title, year):
        query_title = Q(title__iexact=title)
        query_title.add(Q(title_original__iexact=title), Q.OR)
        query_title.add(Q(title_preferred__iexact=title), Q.OR)

        query = Q(query_title)
        query_title.add(Q(year=year), Q.AND)
        
        return Movie.objects.filter(query).all()

    # TODO: no demasiado elegante... 
    # esta funcion es para retrasar las llamadas a imdba
    def sleep_delay(self):
        global SLEEP_DELAY

        if SLEEP_DELAY:
            sleep(SLEEP_DELAY)

    def search_movie_imdb(self, title, year, title_alt=None):
        # 2) Buscamos la pelicula con el año en IMDbPy
        ia = IMDb(reraiseExceptions=True)
        search_results = ia.search_movie('%s (%s)' % (title, year))
        search_result = None

        slugify_title = slugify(title)

        for sr in search_results:
            if 'year' in sr and int(sr['year']) == int(year) and slugify(sr['title']) == slugify_title:
                return sr
        
        self.sleep_delay()
        search_results = ia.search_movie(title)
 
        # TODO: El problema es que el titulo este en español o algo por el estilo... 
        for sr in search_results:
            if 'year' in sr and int(sr['year']) == int(year) and slugify(sr['title']) == slugify_title:
                return sr

        """
        # TODO: Buscamos el titulo por los akas ? esto quizas es muy burro...
        if search_result is None and len(search_results) == 1:
            ia_movie = ia.get_movie(search_results[0].movieID)
            if 'akas' in ia_movie.keys():
                # FIXME: Poner por setting estos ' (Spain)'
                for aka in ia_movie['akas']:
                    if aka == '%s (Spain)' % title:
                        search_result = search_result[0]
                        break
        """

        # Buscamos el titulo por el alt si lo tiene
        if title_alt:
            self.sleep_delay()
            return self.search_movie_imdb(title_alt, year)
        
        # No encontramos ni una...
        return None
    
    def interactive_imdb_search(self, title, year, title_alt=None):
        ia = IMDb(reraiseExceptions=True)
        search_results = ia.search_movie('%s (%s)' % (title, year))
                
        if len(search_results) == 0:
            search_results = ia.search_movie(title)
        
        if len(search_results) == 0 and title_alt:
            return self.interactive_imdb_search(title_alt, year)

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

    def get_or_create_person(self, ia_person):
        local_persons = Person.objects.filter(imdb_id=ia_person.getID()).all()

        if local_persons.count() > 0:
            return local_persons[0]
        
        return Person.objects.create(
            name=ia_person['name'],
            canonical_name=ia_person['canonical name'],
            imdb_id=ia_person.getID(),
        )

    def clean_path_no_extension_and_title(self, title):
        clean_title = title
        if '/' in clean_title:
            clean_title = title.split('/')[-1]
        if '.' in clean_title:
            clean_title = title.split('.')[-1]

        return clean_title.strip()
            

    def get_or_insert_movie(self, r, interactive=False, verbosity=1):
        if verbosity > 1:
            print('Tratando "%s (%s)"...' % (r['title'], r['year']))
        """
        Tenemos que averiguar primero:
        1) Si se trata de una peli original
        2) El archivo donde se almacena si no lo es
        """
        title = r['title']
        title_alt=r['title_preferred'] if 'title_preferred' in r and r['title_preferred'] else None
        storage_name = r['storage_name'] if 'storage_name' in r and r['storage_name'] and r['storage_name'] != 'Original' else None
        is_original = True if not storage_name else False

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

        # 1) Buscamos si ya esta dada de alta la pelicula para ese año en la bbdd
        # search_movie_local_data(self, title, year, storage_name=None, path=None, media_format=None):
        local_movies = self.search_movie_local_data(
            title=title, year=r['year'], 
        )

        if local_movies.count() == 1:
            # 1.1) si la esta, sacamos un mensaje y devolvemos la pelicula (FIN)
            if verbosity > 1:
                print("\tINFO: Ya tenemos una película con el título '%s' del año '%s'" % (title, r['year']))
            
            self.get_or_insert_storage(
                movie=local_movies[0], 
                is_original=is_original, 
                storage_type=storage_type, 
                storage_name=storage_name, 
                path=path, 
                resolution=r['resolution'] if 'resolution' in r and r['resolution'] else None, 
                media_format=media_format, 
                version=r['version'] if 'version' in r and r['version'] else None, 
                verbosity=verbosity
            )

            return local_movies[0]
        elif local_movies.count() > 1:
            print("\tERROR!: Parece que hemos encontrado varias películas con el título '%s' del año '%s'" % (title, r['year']))
            return None

        # 2) Buscamos la pelicula con el año en IMDbPy
        search_result = self.search_movie_imdb(
            title, r['year'], title_alt=title_alt
        )

        if search_result is None:
            if not interactive:
                print('\tERROR!: Parece que no encontramos la pelicula "%s (%s)"' % (title, r['year']))
                return None
            else:
                search_reult = self.interactive_imdb_search(
                    title, r['year'], title_alt=title_alt
                )

        if search_result is None:
            # 2.1) Si no la encontramos, sacamos un mensaje y devolvemos None (FIN)
            print("\tERROR!: Parece que NO encontramos películas con el título '%s' del año '%s'" % (title, r['year']))
            return None
        
        # Tambien puede ocurrirnos que esa pelicula ya este dada de alta
        local_movies = Movie.objects.filter(imdb_id=search_result.movieID).all()

        if local_movies.count() == 0:
            ia = IMDb(reraiseExceptions=True)
            # 2.2.2) Recuperamos la pelicula de IMDbPy
            ia_movie = ia.get_movie(search_result.movieID)

            # Puede que el titulo de la pelicula este mal en el CSV, asi que lo notificamos:
            if ia_movie['title'] != title and verbosity > 1:
                print('\tINFO: El titulo de la pelicula "%s" no corresponde con el cargado del imdb "%s"' % (title, ia_movie['title']))
        
            # 2.2.3) Si r tiene directores, los validamos, si no son los mismos, sacamos mensaje
            if 'director' in r and r['director'] and verbosity > 1:
                if not 'director' in ia_movie.keys():
                    print('\tINFO: No encontramos directores para la pelicula "%s"' % ia_movie['title'])
                else:
                    ia_directors = [p['name'] for p in ia_movie['director']]

                    for director_name in r['director'].split(','):
                        if not director_name in ia_directors:
                            # Esto es para que revises tu csv!!!
                            print("\tINFO: No encontramos el director '%s' en IMDB para la pelicula '%s" % (director_name, title))

            local_movie = self.insert_movie(
                ia_movie, 
                tags=r['tags'].split(',') if 'tags' in r and r['tags'] else [],
                title_original=r['title_original'] if 'title_original' in r and r['title_original'] else None,
                verbosity=verbosity
            )
        else:
            if verbosity > 1:
                print("\tINFO: La pelicula '%s' del año '%s' ya esta dada de alta en la bbdd con el imdb_id '%s'" % (title, r['year'], search_result.movieID))
            local_movie = local_movies[0]
        
        self.get_or_insert_storage(
            movie=local_movie, 
            is_original=is_original, 
            storage_type=storage_type, 
            storage_name=storage_name, 
            path=path, 
            resolution=r['resolution'] if 'resolution' in r and r['resolution'] else None, 
            media_format=media_format, 
            version=r['version'] if 'version' in r and r['version'] else None, 
            verbosity=verbosity
        )

        # 2.6) Devolvemos la pelicula
        return local_movie

    def get_or_insert_storage(self, movie, is_original=True, storage_type=None, storage_name=None, path=None, resolution=None, media_format=None, version=None, verbosity=1):
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
            if verbosity > 1:
                print('\tINFO: Ya tenemos la pelicula "%s" del año "%s" dada de alta con esos datos de almacenamiento!' % (movie.title, movie.year))
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

    def insert_movie(self, ia_movie, tags=[], title_original=None, verbosity=1):
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
        elif verbosity > 1:
            print('\tINFO: No encontramos directores para la pelicula "%s"' % ia_movie['title'])
        
        # 2.2.5) Para cada uno de los escritores (lo mismo que para directores)
        writers = []

        if 'writer' in ia_movie.keys():
            for ia_person in ia_movie['writer']:
                lp = self.get_or_create_person(ia_person)

                if not lp.is_writer:
                    lp.is_writer = True
                    lp.save()
                
                writers.append(lp)
        elif verbosity > 1:
            print('\tINFO: No encontramos escritores para la pelicula "%s"' % ia_movie['title'])
        
        # 2.2.5) Para cada uno de casting (lo mismo que para directores)
        casting = []

        if 'cast' in ia_movie.keys():
            for ia_person in ia_movie['cast']:
                lp = self.get_or_create_person(ia_person)

                if not lp.is_actor:
                    lp.is_actor = True
                    lp.save()
                
                casting.append(lp)
        elif verbosity > 1:
            print('\tINFO: No encontramos casting para la pelicula "%s"' % ia_movie['title'])
        
        # 2.3) Damos de alta la pelicula con los datos recuperados de IMDbPy
        # buscamos el titulo preferido:
        title_preferred = None

        # FIXME: Poner por setting estos ' (Spain)'
        if 'akas' in ia_movie.keys():
            for aka in ia_movie['akas']:
                if ' (Spain)' in aka:
                    title_preferred = aka.replace(' (Spain)', '')
                    break
        
        local_movie = Movie.objects.create(
            title=ia_movie['title'],
            title_original=title_original if not title_original is None and title_original else self.get_original_title(ia_movie),
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
        if 'akas' in ia_movie.keys():
            tagged = True

            for tag in ia_movie['akas']:
                local_movie.title_akas.add(
                    get_first_or_create_tag(
                        TitleAka, title=tag
                    )
                )
            
        if 'genres' in ia_movie.keys():
            tagged = True

            for tag in ia_movie['genres']:
                local_movie.genres.add(
                    get_first_or_create_tag(
                        GenreTag, name=tag
                    )
                )

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

        # TODO: 
        # 2.4) Damos de alta las relaciones entre peliculas y personas de todas las recuperadas antes (directores, escritores, casting...)
        for d in directors:
            MoviePerson.objects.create(
                movie=local_movie,
                person=d,
                role=MoviePerson.RT_DIRECTOR
            )

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

    def get_original_title(self, ia_movie):
        if 'countries' in ia_movie.keys() and 'akas' in ia_movie.keys():
            # print(ia_movie['countries'])
            # print(ia_movie['akas'])
            for country in ia_movie['countries']:
                for aka in ia_movie['akas']:
                    if aka.endswith('(%s)' % country):
                        return aka.replace('(%s)' % country, '').strip()
        
        # TODO: Comentar con perico... el problema es que casi nunca viene bien...
        # return ia_movie['original title']
        return None

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

        if 'imdba_delay' in options and options['imdba_delay'] and options['imdba_delay'][0] > 0:
            global SLEEP_DELAY
            SLEEP_DELAY = options['imdba_delay'][0]
        
        from_title = options['from_title'] if 'from_title' in options and options['from_title'] and len(options['from_title']) > 0 else None
        from_title = ' '.join(from_title) if from_title else None

        interactive = options['interactive']
        verbosity = options['verbosity']
        fieldnames = []

        with open(options['csv_file'][0], newline='') as csvfile:
            csv_reader = csv.DictReader(csvfile, delimiter=csv_delimiter, quotechar=csv_quotechar)
            fieldnames = csv_reader.fieldnames
            for r in csv_reader:
                self.validate(r)
        
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
            for r in csv_reader:
                if from_title and from_title == r['title']:
                    start = True

                if start:
                    try:
                        cur_movie = self.get_or_insert_movie(r, interactive=interactive, verbosity=verbosity)
                        if cur_movie is None:
                            csv_writer_fails.writerow(r)
                        else:
                            csv_writer_done.writerow(r)
                    except:
                        print("Error no esperado:", sys.exc_info()[0])
                        csv_writer_fails.writerow(r)
                        raise
                    finally:
                        self.sleep_delay()

                    if verbosity > 1:
                        print("")
