from asgiref.sync import sync_to_async
from django.utils.html import format_html

from data.models import MoviePerson, Movie
from data.search import movie_search_filter

from homodaba.settings import TBOT_LIMIT_MOVIES

def get_movie_detail_mini_html(movie):
    s = format_html('<b>id:{}</b> <a href="{}"><i>{}</i></a>\n',
        movie.id, 
        'https://www.imdb.com/title/%s' % movie.imdb_id, 
        movie.get_complete_title()
    )
    # '<b>id:%s "%s"</b>\n' % (m.id, m.get_complete_title())
    s = s + movie.get_storage_types_html_tg()

    return s

def get_person_row_html(person):
    if person.imdb_id:
        return ' * <a href="%s" ref="noopener noreferrer">%s</a>\n' % (
            person.get_imdb_url(),
            person,
        )
    
    return ' * %s\n' % person


def get_persons_html(movie, role=None, limit=10, label='Casting:'):
    persons = movie.get_persons(role=role)
    s = ''

    i = 0
    if len(persons) > 0:
        s = '<b>%s</b>\n' % label
        for p in persons:
            i = i + 1
            if limit and i > limit:
                s = s + ' * Hay más resultados, visita imdb o la bbdd para ver el resto...'
                break
            s = s + get_person_row_html(p)
    
    return s

def get_movie_detail_html(movie: Movie):
    s = '<b>id:%s</b> <a href="%s"><i>%s</i></a>\n' % (
        str(movie.id), 
        'https://www.imdb.com/title/%s' % movie.imdb_id, 
        movie.get_complete_title()
    )
    # '<b>id:%s "%s"</b>\n' % (m.id, m.get_complete_title())
    s = s + movie.get_storage_types_html_tg()
    other_titles = movie.get_main_titles()
    if len(other_titles) > 0:
        s = s + '<b>Otros títulos (akas):</b> %s\n' % other_titles

    s = s + get_persons_html(
        movie, role=MoviePerson.RT_DIRECTOR, 
        label='Dirigida por:'
    )

    s = s + get_persons_html(
        movie, role=MoviePerson.RT_WRITER, 
        label='Escrita por:'
    )

    s = s + get_persons_html(
        movie, role=MoviePerson.RT_ACTOR, limit=5
    )

    return s

def get_movies_detail_mini_html(movies):
    s = ''
    for m in movies:
        s = s + get_movie_detail_mini_html(m)
    
    return s

@sync_to_async
def get_movie_detail_html_by_id(id: int):
    movies = Movie.objects.filter(id=id).all()
    if movies.count() == 1:
        return get_movie_detail_html(movies[0])
    
    return "<b>No encontramos la película que buscas.</b>"

@sync_to_async
def search_movies_as_html(search_term):
    movies, use_distinct = movie_search_filter(search_term)
    movies = movies.order_by('title').all()

    if movies.count() == 0:
        return True, """No encontramos películas con el término "%s".""" % search_term
    else:
        s_extra = ""
        if movies.count() > TBOT_LIMIT_MOVIES:
            s_extra = """<b>Hemos encontrado mas de "%s" películas.</b>\n""" % str(TBOT_LIMIT_MOVIES)
        return movies.count() > 1, s_extra + get_movies_detail_mini_html(movies[:TBOT_LIMIT_MOVIES])
