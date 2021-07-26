from django.utils.html import format_html

from data.models import MoviePerson

def get_movie_detail_mini_html(movie):
    s = format_html('<b>id:{}</b> <a href="{}"><i>{}</i></a>\n',
        movie.id, 
        'https://www.imdb.com/title/tt%s' % movie.imdb_id, 
        movie.get_complete_title()
    )
    # '<b>id:%s "%s"</b>\n' % (m.id, m.get_complete_title())
    s = s + movie.get_storage_types_html_tg()

    return s

def get_person_row_html(person):
    if person.imdb_id:
        return ' * <a href="%s">%s</a>\n' % (
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

def get_movie_detail_html(movie):
    s = '<b>id:%s</b> <a href="%s"><i>%s</i></a>\n' % (
        str(movie.id), 
        'https://www.imdb.com/title/tt%s' % movie.imdb_id, 
        movie.get_complete_title()
    )
    # '<b>id:%s "%s"</b>\n' % (m.id, m.get_complete_title())
    s = s + movie.get_storage_types_html_tg()
    other_titles = movie.get_other_titles()
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

def print_movie(movie, update):
    update.message.reply_html(
        get_movie_detail_html(movie)
    )

def print_movies(movies, update):
    s = ''
    for m in movies:
        s = s + get_movie_detail_mini_html(m)
    
    update.message.reply_html(s, disable_web_page_preview=True if movies.count() > 1 else False)