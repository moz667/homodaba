from data.models import Movie
from data.search import movie_search_filter

from homodaba.settings import TBOT_TOKEN, TBOT_LIMIT_MOVIES

from .utils import print_movie, print_movies

import telegram

def start_command(update, context):
    """Send a message when the command /start is issued."""
    bot_info = telegram.Bot(TBOT_TOKEN).get_me()
    update.message.reply_text('Bienvenido a %s!' % bot_info["username"])
    help_command(update, context)

def help_command(update, context):
    if not update:
        return
    update.message.reply_html("""
<b>/help: </b> Muestra este mensaje.
<b>[/search] texto [(año)]: </b> Busca peliculas que coincidan con texto (opcionalmente del año entre parentesis). Si se especifica el texto entre comillas dobles, busca términos exactos.
<b>/list: </b> Lista las primeras 10 péliculas.
<b>/movie id: </b> Muestra el detalle de la película con ese id.
""")

def movie_detail_command(update, context):
    if not update:
        return
    id = update.message.text if update and update.message else None
    if id:
        id = id[len('/movie'):].strip() if id.startswith('/movie') else id
        movies = Movie.objects.filter(id=id).all()
        if movies.count() == 1:
            print_movie(movies[0], update)
        else:
            update.message.reply_text("No encontramos la película que buscas.")

def search_command(update, context):
    if not update:
        return
    search_term = update.message.text if update and update.message else None

    if search_term:
        search_term = search_term[len('/search'):].strip() if search_term.startswith('/search') else search_term
        
        movies = movie_search_filter(search_term).order_by('title').all()

        if movies.count() == 0:
            update.message.reply_text("""No encontramos películas con el término "%s".""" % search_term)
        else:
            if movies.count() > TBOT_LIMIT_MOVIES:
                update.message.reply_text("""Hemos encontrado mas de "%s" películas.""" % str(TBOT_LIMIT_MOVIES))
            print_movies(movies[:TBOT_LIMIT_MOVIES], update)
    else:
        update.message.reply_text("Tienes que introducir algún término de búsqueda")

"""
TODO: Borrar o mejorar: comando antiguo que listaba pelis... no tiene mucho sentido a no 
ser que hagamos alguna paginacion o algo por el estilo.

def list_movies_command(update, context):
    if not update:
        return
    # TODO: hacer algo para resolver el problema
    # de que son muchos, opciones:
    #   - Paginar (creando un boton que pida mas)
    #   - Generar un CSV y mandarlo (poniendolo en MEDIA)
    #       "https://core.telegram.org/bots/api#sending-files"
    update.message.reply_text("El problema con la lista de peliculas es que son demasiadas... asi que solo te voy a sacar las primeras %s" % str(TBOT_LIMIT_MOVIES))
    print_movies(Movie.objects.all()[:TBOT_LIMIT_MOVIES], update)
"""