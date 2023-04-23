from homodaba.settings import CASTING_LIMIT

from data.models import Movie, Person, MovieStorageType, MoviePerson, Tag, GenreTag, TitleAka, ContentRatingTag, Country
from data.models import get_first_or_create_tag, get_or_create_country, populate_movie_auto_tags

from data.utils import Trace as trace
from data.utils.imdbpy_facade import get_imdb_titles, get_imdb_movie

from data.management.commands.utils import normalize_age_certificate

def get_or_create_person_not_an_imdb_movie(name):
    local_persons = Person.objects.filter(name__icontains=name).all()

    if local_persons.count() > 0:
        return local_persons[0]
    
    return Person.objects.create(
        name=name,
        canonical_name=name,
        imdb_id=None,
    )

def get_or_create_person_from_imdb(imdb_person):
    local_persons = Person.objects.filter(imdb_id=imdb_person.getID()).all()

    if local_persons.count() > 0:
        return local_persons[0]

    # Es posible que se haya dado de alta el tipo antes (Con una peli que 
    # no este en el imdb). Para estas actualizamos los datos y devolvemos
    # el primero que encontremos
    local_persons = Person.objects.filter(name=imdb_person['name'], imdb_id=None).all()
    if local_persons.count() > 0:
        for lp in local_persons:
            lp.canonical_name = imdb_person['canonical name']
            lp.imdb_id = imdb_person.getID()

            lp.save()
        
        return local_persons[0]

    return Person.objects.create(
        name=imdb_person['name'],
        canonical_name=imdb_person['canonical name'],
        imdb_id=imdb_person.getID(),
    )

def get_or_insert_storage(movie, is_original=True, storage_type=None, storage_name=None, path=None, resolution=None, media_format=None, version=None):
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

def insert_movie_from_imdb(title, ia_movie, tags=[], title_original=None, title_preferred=None):
    # 2.2.4) Para cada uno de los directores
    directors = []

    if 'director' in ia_movie.keys():
        warning_no_imd_count = 0

        for imdb_person in ia_movie['director']:
            # 2.2.4.1) Buscamos si lo tenemos dado de alta (imdb_id)
            # 2.2.4.1.1) Si lo tenemos dado de alta lo recuperamos de la bbdd
            # 2.2.4.1.2) Si no, lo damos de alta las personas implicadas con los datos basicos (sin recuperar detalle)
            if imdb_person.myID is None:
                warning_no_imd_count = warning_no_imd_count + 1
                continue

            lp = get_or_create_person_from_imdb(imdb_person)

            if not lp.is_director:
                lp.is_director = True
                lp.save()
            
            directors.append(lp)
        
        if warning_no_imd_count > 0:
            trace.warning('\t\t- Director sin imdb id (%s)' % warning_no_imd_count)
    else:
        trace.warning('\tinsert_movie_from_imdb: No encontramos directores para la pelicula "%s"' % title)
    
    # 2.2.5) Para cada uno de los escritores (lo mismo que para directores)
    writers = []

    if 'writer' in ia_movie.keys():
        warning_no_imd_count = 0

        for imdb_person in ia_movie['writer']:
            if imdb_person.myID is None:
                warning_no_imd_count = warning_no_imd_count + 1
                continue

            lp = get_or_create_person_from_imdb(imdb_person)

            if not lp.is_writer:
                lp.is_writer = True
                lp.save()
            
            writers.append(lp)

        if warning_no_imd_count > 0:
            trace.warning('\t\t- Escritor sin imdb id (%s)' % warning_no_imd_count)
    else:
        trace.warning('\tNo encontramos escritores para la pelicula "%s"' % title)
    
    # 2.2.5) Para cada uno de casting (lo mismo que para directores)
    casting = []

    if 'cast' in ia_movie.keys():
        warning_no_imd_count = 0
        i = 0
        for imdb_person in ia_movie['cast']:
            # La alta de personas en la base de datos la hemos limitado para 
            # intentar optimizar un poco el rendimiento. (ver settings para mas 
            # info)
            if not CASTING_LIMIT or i < CASTING_LIMIT:
                if imdb_person.myID is None:
                    warning_no_imd_count = warning_no_imd_count + 1
                    continue

                i = i + 1

                lp = get_or_create_person_from_imdb(imdb_person)

                if not lp.is_actor:
                    lp.is_actor = True
                    lp.save()
                
                casting.append(lp)
            else:
                break

        if warning_no_imd_count > 0:
            trace.warning('\t\t- Casting sin imdb id (%s)' % warning_no_imd_count)
    else:
        trace.warning('\tNo encontramos casting para la pelicula "%s"' % title)

    directors, writers, casting = populate_default_casting(
        directors=directors, writers=writers, casting=casting
    )

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
    )

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
    
    # Completando paises de la peli
    populate_countries(local_movie, ia_movie)

    if 'genres' in ia_movie.keys():
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
            for vc in valid_certs:
                vc_tag = get_first_or_create_tag(
                    ContentRatingTag, name=normalize_age_certificate(vc)
                )

                if not vc_tag in local_movie.content_rating_systems.all():
                    local_movie.content_rating_systems.add(vc_tag)
        else:
            trace.warning('No se encontraron clasificaciones de edad para "%s"' % local_movie.get_complete_title())

    # 2.4) Damos de alta las relaciones entre peliculas y personas de todas las recuperadas antes (directores, escritores, casting...)
    insert_casting_on_local_movie(
        local_movie=local_movie,
        directors=directors,
        writers=writers,
        casting=casting,
    )

    populate_local_movie_tags(local_movie, tags)

    local_movie.save()

    return local_movie

def populate_countries(local_movie, imdb_movie=None):
    if imdb_movie is None and local_movie.imdb_id:
        imdb_movie = get_imdb_movie(local_movie.imdb_id)
    
    if imdb_movie and 'countries' in imdb_movie.keys() and len(imdb_movie['countries']) > 0:
        trace.debug(" * Añadiendo paises para la peli:")
        for c in imdb_movie['countries']:
            trace.debug("    - %s" % c)
            local_movie.countries.add(get_or_create_country(
                country=c
            ))
    else:
        trace.debug(" * Añadiendo '%s' a la peli" % Country.NO_COUNTRY)
        local_movie.countries.add(get_or_create_country(
            country=Country.NO_COUNTRY
        ))

def insert_movie_from_a_not_an_imdb_movie(title, year, directors=[], tags=[], title_original=None, title_preferred=None):
    db_directors = []

    for d in directors:
        lp = get_or_create_person_not_an_imdb_movie(name=d)

        if not lp.is_director:
            lp.is_director = True
            lp.save()
        
        db_directors.append(lp)

    if not title_original:
        title_original = title

    local_movie = Movie.objects.create(
        title=title,
        title_original=title_original,
        title_preferred=title_preferred,
        imdb_id=None,
        kind=Movie.MK_NOT_AN_IMDB_MOVIE,
        summary=None,
        poster_url=None,
        poster_thumbnail_url=None,
        year=year,
        rating=None,
    )

    # Por ahora no tenemos ni writers ni casting en las not_an_imdb_movie
    insert_casting_on_local_movie(
        local_movie=local_movie,
        directors=db_directors,
    )

    populate_local_movie_tags(local_movie, tags)

    # Completando paises de la peli (sin imdb)
    populate_countries(local_movie)

    local_movie.save()

    return local_movie

def populate_local_movie_tags(local_movie, tags=[]):
    if len(tags):
        for tag in tags:
            db_tag = get_first_or_create_tag(
                Tag, name=tag
            )

            if not db_tag in local_movie.tags.all():
                local_movie.tags.add(db_tag)

    populate_movie_auto_tags(local_movie)

def insert_casting_on_local_movie(local_movie, directors=[], writers=[], casting=[]):
    directors, writers, casting = populate_default_casting(
        directors=directors, 
        writers=writers, 
        casting=casting
    )

    # 2.4) Damos de alta las relaciones entre peliculas y personas de todas las recuperadas antes (directores, escritores, casting...)
    for d in directors:
        MoviePerson.objects.create(
            movie=local_movie,
            person=d,
            role=MoviePerson.RT_DIRECTOR
        )
        # Tambien lo damos de alta en el m2m de directors:
        local_movie.directors.add(d)
    
    for w in writers:
        MoviePerson.objects.create(
            movie=local_movie,
            person=w,
            role=MoviePerson.RT_WRITER
        )
        # Tambien lo damos de alta en el m2m de writers:
        local_movie.writers.add(w)

    for c in casting:
        MoviePerson.objects.create(
            movie=local_movie,
            person=c,
            role=MoviePerson.RT_ACTOR
        )
        # Tambien lo damos de alta en el m2m de actors
        local_movie.actors.add(c)

def populate_default_casting(directors=[], writers=[], casting=[]):
    if not len(directors):
        # Si no tiene director creamos una persona que sea Sin Director
        lp = get_or_create_person_not_an_imdb_movie(name=Person.DEFAULT_NO_DIRECTOR)

        if not lp.is_director:
            lp.is_director = True
            lp.save()
        
        directors = [lp]
    
    if not len(writers):
        lp = get_or_create_person_not_an_imdb_movie(name=Person.DEFAULT_NO_WRITER)
        if not lp.is_writer:
            lp.is_writer = True
            lp.save()
        writers = [lp]
    
    if not len(casting):
        lp = get_or_create_person_not_an_imdb_movie(name=Person.DEFAULT_NO_ACTOR)
        if not lp.is_actor:
            lp.is_actor = True
            lp.save()
        casting = [lp]
    
    return directors, writers, casting
