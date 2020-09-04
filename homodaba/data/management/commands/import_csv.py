from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.utils.translation import gettext as _

from data.models import Movie, Person, MovieStorageType, MoviePerson

import csv

from imdb import IMDb

class Command(BaseCommand):
    help = _('Importa datos desde un CSV')

    def validate(self, r):
        # path_no_extension_and_title;title_preferred
        if (not 'title' in r or not r['title']) and (not 'path_no_extension_and_title' in r or not r['path_no_extension_and_title']):
            raise Exception("ERROR!: El titulo es obligatorio y tiene que estar definido en el CSV como 'title'.")
        if not 'year' in r or not r['year']:
            raise Exception("ERROR!: El año de estreno es obligatorio y tiene que estar definido en el CSV como 'year'.")

    def add_arguments(self, parser):
        parser.add_argument('csv_file', nargs='+', type=str)

    def get_person_local_data(self, imdb_id):
        persons = Person.objects.filter(imdb_id=imdb_id).all()

        if persons.count() > 0:
            return persons[0]
        
        return None

    def search_movie_local_data(self, title, year, storage_type=None, storage_name=None, path=None, media_format=None):
        query_title = Q(title__iexact=title)
        query_title.add(Q(title_original__iexact=title), Q.OR)
        query_title.add(Q(title_preferred__iexact=title), Q.OR)

        query = Q(query_title)
        query_title.add(Q(year=year), Q.AND)
        
        return Movie.objects.filter(query).all()

    def get_or_create_person(self, ia_person):
        # TODO: deberia ser solo una :P
        local_person = self.get_person_local_data(ia_person.getID())
        if local_person:
            return local_person
        
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
            

    def get_or_insert_movie(self, r):
        # storage_name;path_no_extension_and_title;title_preferred;director;year;resolution;media_format
        # TODO: En caso del csv de perico:
        # Localizacion;Título Original;Titulo traducido;Director;Año;Resolución;Formato
        #   Localizacion = storage_name
        #   Título Original = path sin extension (se podria utilizar tambien como title, 
        #       pero creo que no hace falta, ademas algunos casos como por ejemplo:
        #       007/007. 01. Dr.No
        #       falla en la busqueda de imdbPy
        #   )
        #   Titulo traducido = title
        #   Director = director
        #   Año = year
        #   Resolucion = resolution
        #   Formato = media_format
        """
        Tenemos que averiguar primero:
        1) Si se trata de una peli original
        2) El archivo donde se almacena si no lo es
        """
        title = r['title'] if 'title' in r else None
        storage_name = r['storage_name'] if 'storage_name' in r and r['storage_name'] and r['storage_name'] != 'Original' else None
        is_original = True if not storage_name else False

        if not title and 'path_no_extension_and_title' in r:
            # Si se trata de los originales podemos usar el path que es el titulo realmente
            if is_original:
                title = r['path_no_extension_and_title']
            else:
                title = self.clean_path_no_extension_and_title(r['path_no_extension_and_title'])

        print('Insertando "%s"...' % title)
        media_format = r['media_format'] if 'media_format' in r and r['media_format'] and r['media_format'] in MovieStorageType.MEDIA_FORMATS_AS_LIST else None

        path = r['path'] if 'path' in r and r['path'] else None
        if not is_original and not path and 'path_no_extension_and_title' in r and r['path_no_extension_and_title']:
            path = r['path_no_extension_and_title']
            if media_format:
                if media_format in MovieStorageType.MEDIA_FORMATS_FILE_WITH_ISO_EXTENSION:
                    path = path + ".iso"
                elif media_format in MovieStorageType.MEDIA_FORMATS_FILE_WITH_OTHER_EXTENSION:
                    path = path + ".%s" % media_format.lower()

        # 1) Buscamos si ya esta dada de alta la pelicula para ese año en la bbdd
        # search_movie_local_data(self, title, year, storage_name=None, path=None, media_format=None):
        local_movies = self.search_movie_local_data(
            title=title, year=r['year'], 
            storage_name=r['storage_name'] if 'storage_name' in r and r['storage_name'] else None

        )
        if local_movies.count() == 1:
            # 1.1) si la esta, sacamos un mensaje y devolvemos la pelicula (FIN)
            print("INFO: Ya tenemos una película con el título '%s' del año '%s'" % (title, r['year']))
            return local_movies[0]
        elif local_movies.count() > 1:
            print("WARNING!: Parece que hemos encontrado varias películas con el título '%s' del año '%s'" % (title, r['year']))
            return None
        # 2) Buscamos la pelicula con el año en IMDbPy
        ia = IMDb()
        search_results = ia.search_movie('%s (%s)' % (title, r['year']))
        search_result = None
        for sr in search_results:
            if ['year', 'title'] in sr and sr['year'] == r['year'] and sr['title'] == title:
                search_result = sr
                break
        
        # Buscamos el titulo por el preferred si lo tiene
        if search_result is None and 'title_preferred' in r:
            search_results = ia.search_movie('%s (%s)' % (r['title_preferred'], r['year']))
            for sr in search_results:
                if ['year', 'title'] in sr and sr['year'] == r['year'] and sr['title'] == title:
                    search_result = sr
                    break

            # Buscamos el titulo por los aka
            if search_result is None and len(search_results) == 1:
                ia_movie = ia.get_movie(search_results[0].movieID)
                # TODO: Poner por setting estos ' (Spain)'
                for aka in ia_movie['akas']:
                    if aka == '%s (Spain)' % title:
                        search_result = search_result[0]
                        break
        
        if search_result is None and len(search_results) > 0:
            print('Parece que no encontramos la pelicula "%s (%s)" ¿Es alguna de estas?:' % (title, r['year']))
            i = 1
            for sr in search_results:
                print("%s) %s (%s)" % (str(i), sr['title'], sr['year']))
                i = i + 1
            print("n) Para continuar con el siguiente")
            print("q) Para salir")

            input_return = ''
            while not input_return:
                input_return = input("")

                if input_return == 'q':
                    print("ERROR!: Parece que NO encontramos películas con el título '%s' del año '%s'" % (title, r['year']))
                    exit()
                elif input_return == 'n':
                    print("ERROR!: Parece que NO encontramos películas con el título '%s' del año '%s'" % (title, r['year']))
                    return None
                else:
                    try:
                        input_return = int(input_return)
                        if not (input_return > 0 and input_return <= len(search_results)):
                            print("ERROR!: Ese valor no es posible.")
                            input_return = ""
                    except ValueError:
                        print("ERROR!: Ese valor no es posible.")
                        input_return = ""
            
            search_result = search_results[int(input_return) - 1]

        if search_result is None:
            # 2.1) Si no la encontramos, sacamos un mensaje y devolvemos None (FIN)
            print("ERROR!: Parece que NO encontramos películas con el título '%s' del año '%s'" % (title, r['year']))
            return None

        # 2.2.2) Recuperamos la pelicula de IMDbPy
        ia_movie = ia.get_movie(search_result.movieID)
        # 2.2.3) Si r tiene directores, los validamos, si no son los mismos, sacamos mensaje
        if 'director' in r and r['director']:
            ia_directors = [p['name'] for p in ia_movie['director']]

            for director_name in r['director'].split(','):
                if not director_name in ia_directors:
                    # Esto es para que revises tu csv!!!
                    print("WARNING! No encontramos el director '%s' en IMDB para la pelicula '%s" % (director_name, title))
        
        # 2.2.4) Para cada uno de los directores
        directors = []

        for ia_person in ia_movie['director']:
            # 2.2.4.1) Buscamos si lo tenemos dado de alta (imdb_id)
            # 2.2.4.1.1) Si lo tenemos dado de alta lo recuperamos de la bbdd
            # 2.2.4.1.2) Si no, lo damos de alta las personas implicadas con los datos basicos (sin recuperar detalle)
            lp = self.get_or_create_person(ia_person)

            if not lp.is_director:
                lp.is_director = True
                lp.save()
            
            directors.append(lp)
        
        # 2.2.5) Para cada uno de los escritores (lo mismo que para directores)
        writers = []

        for ia_person in ia_movie['writer']:
            lp = self.get_or_create_person(ia_person)

            if not lp.is_writer:
                lp.is_writer = True
                lp.save()
            
            writers.append(lp)
        
        # 2.2.5) Para cada uno de casting (lo mismo que para directores)
        casting = []

        for ia_person in ia_movie['cast']:
            lp = self.get_or_create_person(ia_person)

            if not lp.is_actor:
                lp.is_actor = True
                lp.save()
            
            casting.append(lp)
        
        # 2.3) Damos de alta la pelicula con los datos recuperados de IMDbPy
        # buscamos el titulo preferido:
        title_preferred = None

        # TODO: Poner por setting estos ' (Spain)'
        for aka in ia_movie['akas']:
            if ' (Spain)' in aka:
                title_preferred = aka.replace(' (Spain)', '')
                break
        
        # Buscamos 

        movie = Movie.objects.create(
            title=ia_movie['title'],
            title_original=ia_movie['original title'],
            title_preferred=title_preferred,
            imdb_id=ia_movie.getID(),
            kind=ia_movie['kind'],
            summary=ia_movie.summary(),
            poster_url=ia_movie['full-size cover url'],
            poster_thumbnail_url=ia_movie['cover url'],
            year=ia_movie['year'],
            imdb_raw_data=ia_movie.asXML(),
        )

        # TODO:
        # 2.4) Damos de alta las relaciones entre peliculas y personas de todas las recuperadas antes (directores, escritores, casting...)
        # 2.5) Damos de alta la relacion entre pelicula y tipo de almacemaniento (MovieStorageType)
        # 2.6) Devolvemos la pelicula

        return movie

    def handle(self, *args, **options):
        with open(options['csv_file'][0], newline='') as csvfile:
            # TODO: definir delimitadores por settings
            csv_reader = csv.DictReader(csvfile, delimiter=';', quotechar='|')
            for r in csv_reader:
                self.validate(r)

        with open(options['csv_file'][0], newline='') as csvfile:
            # TODO: definir delimitadores por settings
            csv_reader = csv.DictReader(csvfile, delimiter=';', quotechar='|')
            for r in csv_reader:
                self.get_or_insert_movie(r)


"""
TODO: COPYPASTA para el scrapeo
>>> from imdb import IMDb
>>> ia = IMDb()
>>> results = ia.search_movie('the matrix (1999)')
>>> results
[<Movie id:0133093[http] title:_The Matrix (1999)_>, <Movie id:9710398[http] title:_"Oliver Harper's Retrospectives and Reviews" The Matrix (1999) (2019)_>, <Movie id:5310324[http] title:_"Screen Junkies Movie Fights" Pitch the Matrix Sequel - New Year's Eve 1999!! (2016)_>, <Movie id:0211096[http] title:_V-World Matrix (1999) (V)_>, <Movie id:0701636[http] title:_"At the Movies" The Matrix/10 Things I Hate About You/Cookie's Fortune/The Out-of-Towners/The Dreamlife of Angels (1999)_>, <Movie id:0365467[http] title:_Making 'The Matrix' (1999)_>, <Movie id:0438231[http] title:_The Matrix: The Movie Special (1999) (TV)_>, <Movie id:5319308[http] title:_The Matrix: Follow the White Rabbit (1999) (V)_>, <Movie id:0594933[http] title:_"HBO First Look" The Making of 'The Matrix' (1999)_>]
>>> results[0]
<Movie id:0133093[http] title:_The Matrix (1999)_>
>>> results[0].keys()
['title', 'kind', 'year', 'cover url', 'canonical title', 'long imdb title', 'long imdb canonical title', 'smart canonical title', 'smart long imdb canonical title', 'full-size cover url']
>>> results[0]['year']
1999
>>> results[0]['cover url']
'https://m.media-amazon.com/images/M/MV5BNzQzOTk3OTAtNDQ0Zi00ZTVkLWI0MTEtMDllZjNkYzNjNTc4L2ltYWdlXkEyXkFqcGdeQXVyNjU0OTQ0OTY@._V1_UX32_CR0,0,32,44_AL_.jpg'
>>> results[0].movieID
'0133093'
URL DEL IMDB: https://www.imdb.com/title/tt0133093/
>>> the_matrix = ia.get_movie('0133093')
>>> the_matrix.keys()
['original title', 'cast', 'genres', 'runtimes', 'countries', 'country codes', 'language codes', 'color info', 'aspect ratio', 'sound mix', 'box office', 'certificates', 'original air date', 'rating', 'votes', 'cover url', 'imdbID', 'plot outline', 'languages', 'title', 'year', 'kind', 'directors', 'writers', 'producers', 'composers', 'cinematographers', 'editors', 'editorial department', 'casting directors', 'production designers', 'art directors', 'set decorators', 'costume designers', 'make up department', 'production managers', 'assistant directors', 'art department', 'sound department', 'special effects', 'visual effects', 'stunts', 'camera department', 'animation department', 'casting department', 'costume departmen', 'location management', 'music department', 'script department', 'transportation department', 'miscellaneous', 'akas', 'writer', 'director', 'top 250 rank', 'production companies', 'distributors', 'special effects companies', 'other companies', 'plot', 'synopsis', 'canonical title', 'long imdb title', 'long imdb canonical title', 'smart canonical title', 'smart long imdb canonical title', 'full-size cover url']
>>> the_matrix['original title']
'Matrix (1999)'
>>> the_matrix['title']
'The Matrix'
>>> the_matrix['kind']
'movie' # Nos puede servir para diferenciar pelis de series... 
>>> the_matrix['genres']
['Action', 'Sci-Fi']
>>> the_matrix['rating']
8.7
>>> the_matrix['full-size cover url']
'https://m.media-amazon.com/images/M/MV5BNzQzOTk3OTAtNDQ0Zi00ZTVkLWI0MTEtMDllZjNkYzNjNTc4L2ltYWdlXkEyXkFqcGdeQXVyNjU0OTQ0OTY@.jpg'
>>> the_matrix.summary()
'Movie\n=====\nTitle: Matrix, The (1999)\nGenres: Action, Sci-Fi.\nDirector: Lana Wachowski, Lilly Wachowski.\nWriter: Lilly Wachowski, Lana Wachowski.\nCast: Keanu Reeves (Neo), Laurence Fishburne (Morpheus), Carrie-Anne Moss (Trinity), Hugo Weaving (Agent Smith), Gloria Foster (Oracle).\nRuntime: 136.\nCountry: United States.\nLanguage: English.\nRating: 8.7 (1631912 votes).\nPlot: A computer hacker learns from mysterious rebels about the true nature of his reality and his role in the war against its controllers.'
>>> series = ia.get_movie('0389564')
>>> series['kind']
'tv series'
>>> series['title']
'The 4400'
>>> the_matrix['director']
[<Person id:0905154[http] name:_Lana Wachowski_>, <Person id:0905152[http] name:_Lilly Wachowski_>]
>>> the_matrix['director'][0].keys()
['name', 'canonical name', 'long imdb name', 'long imdb canonical name']
>>> the_matrix['director'][0]['name']
'Lana Wachowski'
>>> the_matrix['director'][0]['canonical name']
'Wachowski, Lana'
>>> the_matrix['director'][0]['long imdb name']
'Lana Wachowski'
>>> the_matrix['director'][0]['long imdb canonical name']
'Wachowski, Lana'
>>> the_matrix['director'][0].getID()
'0905154'
URL DEL IMDB: https://www.imdb.com/name/nm0905154/
>>> lana = ia.get_person('0905154')
>>> lana.keys()
['birth info', 'headshot', 'akas', 'filmography', 'imdbID', 'name', 'birth name', 'height', 'mini biography', 'spouse', 'trade mark', 'trivia', 'quotes', 'salary history', 'birth date', 'birth notes', 'canonical name', 'long imdb name', 'long imdb canonical name', 'full-size headshot']
>>> lana['headshot']
'https://m.media-amazon.com/images/M/MV5BMjEzMTc2MDQ5OV5BMl5BanBnXkFtZTcwNjkzNDY0OA@@._V1_UX67_CR0,0,67,98_AL_.jpg'
>>> lana['full-size headshot']
'https://m.media-amazon.com/images/M/MV5BMjEzMTc2MDQ5OV5BMl5BanBnXkFtZTcwNjkzNDY0OA@@.jpg'
"""