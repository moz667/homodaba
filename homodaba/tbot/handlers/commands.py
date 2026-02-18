from homodaba.settings import TBOT_TOKEN

from .utils import get_movie_detail_html_by_id, search_movies_as_html

import telegram
from telegram import Update
from telegram.ext import ContextTypes

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # """Send a message when the command /start is issued."""
    bot_info = await telegram.Bot(TBOT_TOKEN).get_me()
    await update.message.reply_text(f"Bienvenido a {bot_info.username}!")
    await help_command(update, context)

async def help_command(update, context):
    if not update:
        return
    await update.message.reply_html("""
<b>/help: </b> Muestra este mensaje.
<b>[/search] texto: </b> Busca peliculas que coincidan con texto. Si se especifica el texto entre comillas dobles, busca términos exactos.
<b>/movie id: </b> Muestra el detalle de la película con ese id.
""")

async def movie_detail_command(update, context):
    if not update:
        return

    id = update.message.text if update and update.message else None

    if id:
        id = id[len('/movie'):].strip() if id.startswith('/movie') else id
        movie_detail_html = await get_movie_detail_html_by_id(id)
        await update.message.reply_html(movie_detail_html)

async def search_command(update, context):
    if not update:
        return
    search_term = update.message.text if update and update.message else None

    if search_term:
        search_term = search_term[len('/search'):].strip() if search_term.startswith('/search') else search_term
        disable_web_page_preview, search_movies_html = await search_movies_as_html(search_term)
        await update.message.reply_html(search_movies_html, disable_web_page_preview=disable_web_page_preview)
    else:
       await update.message.reply_text("Tienes que introducir algún término de búsqueda")
