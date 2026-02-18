import asyncio

from data.models import Movie
from data.search import movie_search_filter

from asgiref.sync import sync_to_async
from homodaba.settings import TBOT_TOKEN, TBOT_LIMIT_MOVIES

from .utils import print_movie, print_movies

import telegram
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

help_message = """
<b>/help: </b> Muestra este mensaje.
<b>[/search] texto [(año)]: </b> Busca peliculas que coincidan con texto (opcionalmente del año entre parentesis). Si se especifica el texto entre comillas dobles, busca términos exactos.
<b>/movie id: </b> Muestra el detalle de la película con ese id.
"""

def sync_print_reply_text(update: Update, message):
    asyncio.run(update.message.reply_text(message))

def sync_print_reply_html(update: Update, message):
    asyncio.run(update.message.reply_html(message))


@sync_to_async
def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # """Send a message when the command /start is issued."""
    bot_info = asyncio.run(telegram.Bot(TBOT_TOKEN).get_me())
    sync_print_reply_text(update, f"Bienvenido a {bot_info.username}!")
    sync_print_reply_html(update, help_message)

@sync_to_async
def help_command(update, context):
    if not update:
        return
    asyncio.run(update.message.reply_html("""
<b>/help: </b> Muestra este mensaje.
<b>[/search] texto [(año)]: </b> Busca peliculas que coincidan con texto (opcionalmente del año entre parentesis). Si se especifica el texto entre comillas dobles, busca términos exactos.
<b>/movie id: </b> Muestra el detalle de la película con ese id.
"""))

@sync_to_async
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
            asyncio.run(update.message.reply_text("No encontramos la película que buscas."))

@sync_to_async
def search_command(update, context):
    if not update:
        return
    search_term = update.message.text if update and update.message else None

    if search_term:
        search_term = search_term[len('/search'):].strip() if search_term.startswith('/search') else search_term
        
        movies, use_distinct = movie_search_filter(search_term)
        movies = movies.order_by('title').all()

        if movies.count() == 0:
           asyncio.run(update.message.reply_text("""No encontramos películas con el término "%s".""" % search_term))
        else:
            if movies.count() > TBOT_LIMIT_MOVIES:
                asyncio.run(update.message.reply_text("""Hemos encontrado mas de "%s" películas.""" % str(TBOT_LIMIT_MOVIES)))
            print_movies(movies[:TBOT_LIMIT_MOVIES], update)
    else:
       asyncio.run(update.message.reply_text("Tienes que introducir algún término de búsqueda"))
