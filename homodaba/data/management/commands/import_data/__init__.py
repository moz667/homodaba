from homodaba.settings import CASTING_LIMIT

from data.models import Movie, Person, MovieStorageType, MoviePerson, Tag, GenreTag, TitleAka, ContentRatingTag, Country
from data.models import get_first_or_create_tag, get_or_create_country, populate_movie_auto_tags

from data.utils import Trace as trace
from data.utils.imdbpy_facade import get_facade_movie
from data.utils.facade_model import FacadeMovie, FacadeCredit

from data.management.commands.utils import normalize_age_certificate

def get_or_create_person_by_name(name):
    local_persons = Person.objects.filter(name__icontains=name).all()

    if local_persons.count() > 0:
        return local_persons[0]
    
    return Person.objects.create(
        name=name,
        canonical_name=name,
        imdb_id=None,
        tmdb_id=None,
    )

def get_person_from_facade_credit(facade_credit: FacadeCredit):
    kargs = {}

    if facade_credit.imdb_id:
        kargs['imdb_id'] = facade_credit.imdb_id

    if facade_credit.tmdb_id:
        kargs['tmdb_id'] = facade_credit.tmdb_id
    
    if facade_credit.name:
        kargs['name'] = facade_credit.name
    
    if len(kargs) > 0:
        local_persons = Person.objects.filter(**kargs).all()

        if local_persons.count() > 0:
            return local_persons[0]

    return None

def get_or_create_person_from_facade_credit(facade_credit: FacadeCredit):
    local_person = get_person_from_facade_credit(facade_credit=facade_credit)

    if local_person:
        return local_person

    return Person.objects.create(
        name=facade_credit.name,
        canonical_name=facade_credit.canonical_name,
        imdb_id=facade_credit.imdb_id,
        tmdb_id=facade_credit.tmdb_id,
        avatar_thumbnail_url=facade_credit.avatar_thumbnail_url,
        avatar_url=facade_credit.avatar_url,
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

def is_valid_facade_credit_for_insert(facade_credit: FacadeCredit):
    return (facade_credit.imdb_id or facade_credit.tmdb_id) and facade_credit.name \
        and facade_credit.canonical_name

def insert_movie_from_facade_movie(title, facade_movie:FacadeMovie, tags=[], title_original=None, title_preferred=None):
    # 2.2.4) Para cada uno de los directores
    directors = []

    if len(facade_movie.directors) > 0:
        warning_not_valid_person = 0

        for facade_credit in facade_movie.directors:
            # 2.2.4.1) Buscamos si lo tenemos dado de alta (imdb_id)
            # 2.2.4.1.1) Si lo tenemos dado de alta lo recuperamos de la bbdd
            # 2.2.4.1.2) Si no, lo damos de alta las personas implicadas con los datos basicos (sin recuperar detalle)
            if not is_valid_facade_credit_for_insert(facade_credit):
                warning_not_valid_person = warning_not_valid_person + 1
                continue

            lp = get_or_create_person_from_facade_credit(facade_credit)

            if not lp.is_director:
                lp.is_director = True
                lp.save()
            
            directors.append(lp)
        
        if warning_not_valid_person > 0:
            trace.warning('\t\t- Director no valido (%s)' % warning_not_valid_person)
    else:
        trace.warning('\tinsert_movie_from_facade_movie: No encontramos directores para la pelicula "%s"' % title)
    
    # 2.2.5) Para cada uno de los escritores (lo mismo que para directores)
    writers = []

    if len(facade_movie.writers) > 0:
        warning_not_valid_person = 0

        for facade_credit in facade_movie.writers:
            if not is_valid_facade_credit_for_insert(facade_credit):
                warning_not_valid_person = warning_not_valid_person + 1
                continue

            lp = get_or_create_person_from_facade_credit(facade_credit)

            if not lp.is_writer:
                lp.is_writer = True
                lp.save()
            
            writers.append(lp)

        if warning_not_valid_person > 0:
            trace.warning('\t\t- Escritor no valido (%s)' % warning_not_valid_person)
    else:
        trace.warning('\tNo encontramos escritores para la pelicula "%s"' % title)
    
    # 2.2.5) Para cada uno de casting (lo mismo que para directores)
    casting = []

    if len(facade_movie.actors) > 0:
        warning_not_valid_person = 0
        i = 0
        for facade_credit in facade_movie.actors:
            # La alta de personas en la base de datos la hemos limitado para 
            # intentar optimizar un poco el rendimiento. (ver settings para mas 
            # info)
            if not CASTING_LIMIT or i < CASTING_LIMIT:
                if not is_valid_facade_credit_for_insert(facade_credit):
                    warning_not_valid_person = warning_not_valid_person + 1
                    continue

                i = i + 1

                lp = get_or_create_person_from_facade_credit(facade_credit)

                if not lp.is_actor:
                    lp.is_actor = True
                    lp.save()
                
                casting.append(lp)
            else:
                break

        if warning_not_valid_person > 0:
            trace.warning('\t\t- Casting no valido (%s)' % warning_not_valid_person)
    else:
        trace.warning('\tNo encontramos casting para la pelicula "%s"' % title)

    directors, writers, casting = populate_default_casting(
        directors=directors, writers=writers, casting=casting
    )

    # TODO: Que hacemos aqui... ponemos el titulo del csv o el de facade_movie?
    local_movie = Movie.objects.create(
        title=facade_movie.title,
        title_original=facade_movie.title_original,
        title_preferred=facade_movie.title_preferred,
        imdb_id=facade_movie.imdb_id,
        tmdb_id=facade_movie.tmdb_id,
        kind=facade_movie.kind,
        summary=facade_movie.summary,
        poster_url=facade_movie.poster_url,
        poster_thumbnail_url=facade_movie.poster_thumbnail_url,
        year=facade_movie.year,
        rating=facade_movie.rating,
    )

    if len(facade_movie.title_akas) > 0:
        title_akas = facade_movie.title_akas
        for key in title_akas.keys():
            key_parts = key.split('_')
            country = key_parts[0]
            title_type = key_parts[1] if len(key_parts) > 1 else None

            trace.debug("    - %s [%s] (%s)" % (title_akas[key], country, title_type))
        
            db_title_aka = get_first_or_create_tag(
                TitleAka, title=title_akas[key], country=country, title_type=title_type
            )
            
            match = False
            for ta in local_movie.title_akas.all():
                if ta.id == db_title_aka.id:
                    match = True
                    break
            
            if not match:
                local_movie.title_akas.add(db_title_aka)
    
    # Completando paises de la peli
    populate_countries(local_movie, facade_movie=facade_movie)

    for tag in facade_movie.genres:
        local_movie.genres.add(
            get_first_or_create_tag(
                GenreTag, name=tag
            )
        )

    if len(facade_movie.content_rating_systems) > 0:
        for c in facade_movie.content_rating_systems:
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

def populate_countries(local_movie, facade_movie: FacadeMovie=None):
    if facade_movie is None and (local_movie.imdb_id or local_movie.tmdb_id):
        facade_movie = get_facade_movie(imdb_id=local_movie.imdb_id, tmdb_id=local_movie.tmdb_id)
    
    if len(facade_movie.countries) > 0:
        trace.debug(" * Añadiendo paises para la peli:")
        for c in facade_movie.countries:
            trace.debug("    - %s" % c)
            # TODO: Convertir desde iso a nombre
            local_movie.countries.add(get_or_create_country(
                country=c
            ))
    else:
        trace.debug(" * Añadiendo '%s' a la peli" % Country.NO_COUNTRY)
        local_movie.countries.add(get_or_create_country(
            country=Country.NO_COUNTRY
        ))

def insert_movie_from_a_not_an_imdb_movie(title, year, directors: list[str]=[], tags: list[str]=[], title_original=None, title_preferred=None):
    db_directors = []

    for director_name in directors:
        lp = get_or_create_person_by_name(name=director_name)

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
        tmdb_id=None,
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
        lp = get_or_create_person_by_name(name=Person.DEFAULT_NO_DIRECTOR)

        if not lp.is_director:
            lp.is_director = True
            lp.save()
        
        directors = [lp]
    
    if not len(writers):
        lp = get_or_create_person_by_name(name=Person.DEFAULT_NO_WRITER)
        if not lp.is_writer:
            lp.is_writer = True
            lp.save()
        writers = [lp]
    
    if not len(casting):
        lp = get_or_create_person_by_name(name=Person.DEFAULT_NO_ACTOR)
        if not lp.is_actor:
            lp.is_actor = True
            lp.save()
        casting = [lp]
    
    return directors, writers, casting
