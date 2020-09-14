from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.utils.translation import gettext as _

from django.utils.html import format_html

from data.models import Movie, Person, MovieStorageType, MoviePerson
from data.search import movie_search_filter

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

import csv
import os
import logging

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

TBOT_TOKEN = 'TBOT_TOKEN'
LIMIT_MOVIES = 50

class Command(BaseCommand):
    help = _('Arranca el bot the telegram')
    home_name = 'homodaba'

    tg_update = None

    def add_arguments(self, parser):
        parser.add_argument('--token', type=str, help="""Token de la API de 
telegram, https://core.telegram.org/bots#6-botfather. (Tambien se puede 
conseguir de la variable de entorno "%s" """ % TBOT_TOKEN)
        parser.add_argument('--home-name', type=str, help="""Nombre de la base
de datos (actualmente "%s") """ % self.home_name)
    
    def start(self, update, context):
        """Send a message when the command /start is issued."""
        update.message.reply_text('Bienvenido a %s!' % self.home_name)
        self.help_command(update, context)

    def help_command(self, update, context):
        if not update:
            return
        update.message.reply_html("""
<b>/help: </b> Muestra este mensaje.
<b>[/search] texto [(año)]: </b> Busca peliculas que coincidan con texto (opcionalmente del año entre parentesis). Si se especifica el texto entre comillas dobles, busca términos exactos.
<b>/list: </b> Lista las primeras 50 péliculas.
<b>/movie id: </b> Muestra el detalle de la película con ese id.
""")

    def get_movie_detail_mini_html(self, movie):
        s = format_html('<b>id:{}</b> <a href="{}"><i>{}</i></a>\n',
            movie.id, 
            'https://www.imdb.com/title/tt%s' % movie.imdb_id, 
            movie.get_complete_title()
        )
        # '<b>id:%s "%s"</b>\n' % (m.id, m.get_complete_title())
        s = s + movie.get_storage_types_html_tg()

        return s

    def get_person_row_html(self, person):
        if person.imdb_id:
            return ' * <a href="%s">%s</a>\n' % (
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
                    s = s + ' * Hay más resultados, visita imdb o la bbdd para ver el resto...'
                    break
                s = s + self.get_person_row_html(p)
        
        return s

    def get_movie_detail_html(self, movie):
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

        logger.debug(s)

        return s

    def print_movie(self, movie, update):
        update.message.reply_html(
            self.get_movie_detail_html(movie)
        )

    def print_movies(self, movies, update):
        s = ''
        for m in movies:
            s = s + self.get_movie_detail_mini_html(m)
        
        update.message.reply_html(s, disable_web_page_preview=True if movies.count() > 1 else False)

    def movie_detail(self, update, context):
        if not update:
            return
        id = update.message.text if update and update.message else None
        if id:
            id = id[len('/movie'):].strip() if id.startswith('/movie') else id
            movies = Movie.objects.filter(id=id).all()
            if movies.count() == 1:
                self.print_movie(movies[0], update)
            else:
                update.message.reply_text("No encontramos la película que buscas.")

    def list_movies(self, update, context):
        if not update:
            return
        # TODO: hacer algo para resolver el problema
        # de que son muchos, opciones:
        #   - Paginar (creando un boton que pida mas)
        #   - Generar un CSV y mandarlo (poniendolo en MEDIA)
        #       "https://core.telegram.org/bots/api#sending-files"
        update.message.reply_text("""El problema con la lista de peliculas es que son demasiadas... asi que solo te voy a sacar las primeras %s""" % str(LIMIT_MOVIES))
        self.print_movies(Movie.objects.all()[:LIMIT_MOVIES], update)

    def search(self, update, context):
        if not update:
            return
        search_term = update.message.text if update and update.message else None

        if search_term:
            search_term = search_term[len('/search'):].strip() if search_term.startswith('/search') else search_term
            
            movies = movie_search_filter(search_term).order_by('title').all()

            if movies.count() == 0:
                update.message.reply_text("""No encontramos películas con el término "%s".""" % search_term)
            else:
                if movies.count() > LIMIT_MOVIES:
                    update.message.reply_text("""Hemos encontrado mas de "%s" películas.""" % str(LIMIT_MOVIES))
                self.print_movies(movies[:LIMIT_MOVIES], update)
        else:
            update.message.reply_text("Tienes que introducir algún término de búsqueda")

    def handle(self, *args, **options):
        token = os.getenv(TBOT_TOKEN, False)
        if not token and (not 'token' in options or not options['token']):
            self.print_help('manage.py', __name__)
            return

        token = options['token'] if 'token' in options else token
      
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
        
        """Start the bot."""
        # Create the Updater and pass it your bot's token.
        # Make sure to set use_context=True to use the new context based callbacks
        # Post version 12 this will no longer be necessary
        updater = Updater(token, use_context=True)

        # Get the dispatcher to register handlers
        dp = updater.dispatcher

        # on different commands - answer in Telegram
        dp.add_handler(CommandHandler("start", self.start))
        dp.add_handler(CommandHandler("search", self.search))
        dp.add_handler(CommandHandler("list", self.list_movies))
        dp.add_handler(CommandHandler("movie", self.movie_detail))
        dp.add_handler(CommandHandler("help", self.help_command))

        # on noncommand i.e message - echo the message on Telegram
        dp.add_handler(MessageHandler(Filters.text & ~Filters.command, self.search))

        # Start the Bot
        updater.start_polling()

        # Run the bot until you press Ctrl-C or the process receives SIGINT,
        # SIGTERM or SIGABRT. This should be used most of the time, since
        # start_polling() is non-blocking and will stop the bot gracefully.
        updater.idle()
