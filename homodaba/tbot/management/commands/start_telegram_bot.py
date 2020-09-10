from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.utils.translation import gettext as _

from data.models import Movie, Person, MovieStorageType, MoviePerson
from data.models import movie_search_filter

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
        """TODO: mensaje de ayuda"""
        update.message.reply_text('TODO: DISPLAY HELP!')

    def print_movies(self, movies, update):
        s = ''
        for m in movies:
            s = s + 'id:%s "%s"\n' % (m.id, m.get_complete_title())
            s = s + m.get_storage_types_text()

        update.message.reply_text(s)

    def list_movies(self, update, context):
        # TODO: hacer algo para resolver el problema
        # de que son muchos, opciones:
        #   - Paginar (creando un boton que pida mas)
        #   - Generar un CSV y mandarlo (o ponerlo en algun sitio si no permite)
        #       "https://core.telegram.org/bots/api#sending-files"
        update.message.reply_text("""El problema con la lista de peliculas es 
que son demasiadas... asi que solo te voy a sacar las primeras %s""" % str(LIMIT_MOVIES))
        self.print_movies(Movie.objects.all()[:LIMIT_MOVIES], update)

    def search(self, update, context):
        if not update or not update.message or not update.message.text:
            return self.list_movies(update, context)
        
        search_term = update.message.text
        movies = movie_search_filter(search_term).all()

        if movies.count() == 0:
            update.message.reply_text("""No encontramos películas con el término "%s".""" % search_term)
        elif movies.count() > LIMIT_MOVIES:
            update.message.reply_text("""Hemos encontrado mas de "%s" películas.""" % str(LIMIT_MOVIES))
            self.print_movies(movies[:LIMIT_MOVIES], update)
        else:
            self.print_movies(movies, update)
        # update.message.reply_text('TODO: SEARCH MOVIES!')
        # update.message.reply_text(update.message.text)

    def handle(self, *args, **options):
        token = os.getenv(TBOT_TOKEN, False)
        if not token and (not 'token' in options or not options['token']):
            self.print_help('manage.py', __name__)
            return

        token = options['token'] if 'token' in options else token
      
        self.home_name = options['home_name'] if 'home_name' in options and options['home_name'] else self.home_name
        
        """Start the bot."""
        # Create the Updater and pass it your bot's token.
        # Make sure to set use_context=True to use the new context based callbacks
        # Post version 12 this will no longer be necessary
        updater = Updater(token, use_context=True)

        # Get the dispatcher to register handlers
        dp = updater.dispatcher

        # on different commands - answer in Telegram
        dp.add_handler(CommandHandler("start", self.start))
        dp.add_handler(CommandHandler("help", self.help_command))
        dp.add_handler(CommandHandler("list", self.list_movies))
        dp.add_handler(CommandHandler("search", self.search))

        # on noncommand i.e message - echo the message on Telegram
        dp.add_handler(MessageHandler(Filters.text & ~Filters.command, self.search))

        # Start the Bot
        updater.start_polling()

        # Run the bot until you press Ctrl-C or the process receives SIGINT,
        # SIGTERM or SIGABRT. This should be used most of the time, since
        # start_polling() is non-blocking and will stop the bot gracefully.
        updater.idle()
