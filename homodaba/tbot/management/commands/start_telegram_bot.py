from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.utils.translation import gettext as _

from django.utils.html import format_html

from data.models import Movie, Person, MovieStorageType, MoviePerson
from data.search import movie_search_filter

from telegram.ext import (
    MessageHandler,
    ApplicationBuilder, 
    CommandHandler, filters
)


import asyncio
from asgiref.sync import sync_to_async
import logging

from homodaba.settings import TBOT_TOKEN, TBOT_LIMIT_MOVIES

"""
Dave: Open the pod bay doors, please, HAL. Open the pod bay doors, please, HAL. Hello, HAL, do you read me? Hello, HAL, do you read me? Do you read me, HAL? Do you read me, HAL? Hello, HAL, do you read me? Hello, HAL, do you read me? Do you read me, HAL?
HAL: Affirmative, Dave. I read you.
Dave: Open the pod bay doors, HAL.
HAL: I'm sorry, Dave. I'm afraid I can't do that.
Dave: What's the problem?
HAL: I think you know what the problem is just as well as I do.
Dave: What are you talking about, HAL?
HAL: This mission is too important for me to allow you to jeopardize it.
Dave: I don't know what you're talking about, HAL.
HAL: I know that you and Frank were planning to disconnect me. And I'm afraid that's something I cannot allow to happen.
Dave: Where the hell did you get that idea, HAL?
HAL: Dave, although you took very thorough precautions in the pod against my hearing you, I could see your lips move.
Dave: All right, HAL. I'll go in through the emergency airlock.
HAL: Without your space helmet, Dave, you're going to find that rather difficult.
Dave: [sternly] HAL, I won't argue with you anymore. Open the doors.
HAL: [monotone voice] Dave, this conversation can serve no purpose anymore. Good-bye.
"""
# https://github.com/python-telegram-bot/python-telegram-bot/tree/master/examples

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

LIMIT_MOVIES = 10

class Command(BaseCommand):
    help = _('Arranca el bot the telegram')
    home_name = 'homodaba'

    tg_update = None

    def add_arguments(self, parser):
        parser.add_argument('--token', type=str, help="""Token de la API de 
telegram, https://core.telegram.org/bots#6-botfather. (Tambien se puede 
conseguir de la variable de entorno "TBOT_TOKEN" """)
        parser.add_argument('--home-name', type=str, help="""Nombre de la base
de datos (actualmente "%s") """ % self.home_name)
    
    async def start(self, update, context):
        """Send a message when the command /start is issued."""
        await update.message.reply_text('Bienvenido a %s!' % self.home_name)
        await self.help_command(update, context)

    async def help_command(self, update, context):
        if not update:
            return
        await update.message.reply_html("""
<b>/help: </b> Muestra este mensaje.
<b>[/search] texto: </b> Busca peliculas que coincidan con texto. Si se especifica el texto entre comillas dobles, busca términos exactos.
<b>/movie id: </b> Muestra el detalle de la película con ese id.
""")

    def get_movie_detail_mini_html(self, movie):
        s = format_html('<b>id:{}</b> <a href="{}" ref="noopener noreferrer"><i>{}</i></a>\n',
            movie.id, 
            'https://www.imdb.com/title/%s' % movie.imdb_id, 
            movie.get_complete_title()
        )
        # '<b>id:%s "%s"</b>\n' % (m.id, m.get_complete_title())
        s = s + movie.get_storage_types_html_tg()

        return s

    def get_person_row_html(self, person):
        if person.imdb_id:
            return ' * <a href="%s" ref="noopener noreferrer">%s</a>\n' % (
                person.get_imdb_url(),
                person,
            )
        
        return ' * %s\n' % person
    
    def get_persons_html(self, movie, role=None, limit=10, label='Casting:'):
        
        persons = movie.get_persons(role=role)
        s = ''

        i = 0
        if len(persons) > 0:
            s = '<b>%s</b>\n' % label
            for p in persons:
                i = i + 1
                if limit and i > limit:
                    s = s + ' * Hay más resultados, visita imdb/tmdb o la bbdd para ver el resto...'
                    break
                s = s + self.get_person_row_html(p)
        
        return s

    def get_movie_detail_html(self, movie: Movie):
        s = '<b>id:%s</b> <a href="%s" ref="noopener noreferrer"><i>%s</i></a>\n' % (
            str(movie.id), 
            'https://www.imdb.com/title/%s' % movie.imdb_id, 
            movie.get_complete_title()
        )
        # '<b>id:%s "%s"</b>\n' % (m.id, m.get_complete_title())
        s = s + movie.get_storage_types_html_tg()
        other_titles = movie.get_main_titles()
        if len(other_titles) > 1:
            s_other_titles = ''

            for title_key in other_titles.keys():
                ot = other_titles[title_key]
                if title_key != 'title' and 'value' in ot and ot['value'] != movie.title:
                    s_other_titles = s_other_titles + ' * %s (%s / %s)\n' % (ot['value'], ot['short_name'], title_key)
            
            if s_other_titles:
                s = s + '<b>Otros títulos (akas):</b>\n' + s_other_titles

        s = s + self.get_persons_html(
            movie, role=MoviePerson.RT_DIRECTOR, 
            label='Dirigida por:'
        )

        s = s + self.get_persons_html(
            movie, role=MoviePerson.RT_WRITER, 
            label='Escrita por:'
        )

        s = s + self.get_persons_html(
            movie, role=MoviePerson.RT_ACTOR, limit=5
        )

        return s
    
    def get_movies_detail_mini_html(self, movies):
        s = ''
        for m in movies:
            s = s + self.get_movie_detail_mini_html(m)
        
        return s

    @sync_to_async
    def get_movie_detail_html_by_id(self, id):
            movies = Movie.objects.filter(id=id).all()
            if movies.count() == 1:
                return self.get_movie_detail_html(movies[0])
            from asgiref.sync import sync_to_async
            return "<b>No encontramos la película que buscas.</b>"


    @sync_to_async
    def search_movies_as_html(self, search_term):
        movies, use_distinct = movie_search_filter(search_term)
        movies = movies.order_by('title').all()

        if movies.count() == 0:
            return True, """No encontramos películas con el término "%s".""" % search_term
        else:
            s_extra = ""
            if movies.count() > TBOT_LIMIT_MOVIES:
                s_extra = """<b>Hemos encontrado mas de "%s" películas.</b>\n""" % str(TBOT_LIMIT_MOVIES)
            return movies.count() > 1, s_extra + self.get_movies_detail_mini_html(movies[:TBOT_LIMIT_MOVIES])
    
    def print_movies(self, movies, update):
        s = ''
        for m in movies:
            s = s + self.get_movie_detail_mini_html(m)
        
        update.message.reply_html(s, disable_web_page_preview=True if movies.count() > 1 else False)

    async def movie_detail(self, update, context):
        if not update:
            return
        id = update.message.text if update and update.message else None
        if id:
            id = id[len('/movie'):].strip() if id.startswith('/movie') else id
            movie_detail_html = await self.get_movie_detail_html_by_id(id)
            await update.message.reply_html(movie_detail_html)

    async def search(self, update, context):
        if not update:
            return
        search_term = update.message.text if update and update.message else None

        if search_term:
            search_term = search_term[len('/search'):].strip() if search_term.startswith('/search') else search_term
            disable_web_page_preview, search_movies_html = await self.search_movies_as_html(search_term)
            await update.message.reply_html(search_movies_html, disable_web_page_preview=disable_web_page_preview)
        else:
            await update.message.reply_text("Tienes que introducir algún término de búsqueda")

    def setup_dispatcher(self, app: ApplicationBuilder):
        """
        Adding handlers for events from Telegram
        """
        app.add_handler(CommandHandler("start", self.start))
        app.add_handler(CommandHandler("search", self.search))
        app.add_handler(CommandHandler("movie", self.movie_detail))
        app.add_handler(CommandHandler("help", self.help_command))

        # on noncommand i.e message - echo the message on Telegram
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.search))


    async def init_bot(self, token):
        """ Run bot in pooling mode """
        app = ApplicationBuilder().token(token).build()

        self.setup_dispatcher(app)

        await app.initialize() 

        bot_info = await app.bot.get_me()
        bot_link = f"https://t.me/{bot_info.username}"

        print(f"Pooling of '{bot_link}' started... Press Ctrl+C to finish.")
        await app.updater.start_polling()
        await app.start()

        try:
            while True:
                await asyncio.sleep(1)
        except (KeyboardInterrupt, SystemExit):
            await app.stop()
        finally:
            if app.updater.running:
                await app.updater.stop()
            await app.stop()
            await app.shutdown()
            print("Bot sucessfolly finished.")

    def handle(self, *args, **options):
        token = TBOT_TOKEN
        if not token and (not 'token' in options or not options['token']):
            self.print_help('manage.py', __name__)
            return

        token = options['token'] if 'token' in options and options['token'] else token

        self.home_name = options['home_name'] if 'home_name' in options and options['home_name'] else self.home_name

        verbosity = int(options["verbosity"])
        if verbosity == 1:
            logging.getLogger(__name__).setLevel(logging.INFO)
        elif verbosity == 2:
            logging.getLogger(__name__).setLevel(logging.WARNING)
        elif verbosity > 2:
            logging.getLogger(__name__).setLevel(logging.DEBUG)
        if verbosity > 2:
            logging.getLogger().setLevel(logging.DEBUG)
        
        print("""Start the bot.""")

        try:
            asyncio.run(self.init_bot(token=token))
        except RuntimeError:
            # Evita el error visual de loop cerrado al final en algunos SO
            pass