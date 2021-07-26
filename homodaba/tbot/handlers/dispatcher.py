"""
    Telegram event handlers
"""

import telegram
from telegram.ext import (
    Updater, Dispatcher, Filters,
    CommandHandler, MessageHandler,
    InlineQueryHandler, CallbackQueryHandler,
    ChosenInlineResultHandler,
)

from homodaba.settings import TBOT_TOKEN

from .commands import start_command, search_command, movie_detail_command, help_command


def setup_dispatcher(dp):
    """
    Adding handlers for events from Telegram
    """
    dp.add_handler(CommandHandler("start", start_command))
    dp.add_handler(CommandHandler("search", search_command))
    # TODO: Por ahora pasamos que no tiene mucho sentido la lista de pelis
    # dp.add_handler(CommandHandler("list", list_movies_command))
    dp.add_handler(CommandHandler("movie", movie_detail_command))
    dp.add_handler(CommandHandler("help", help_command))

    # on noncommand i.e message - echo the message on Telegram
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, search_command))

    return dp


def init_bot():
    """ Run bot in pooling mode """
    updater = Updater(TBOT_TOKEN, use_context=True)

    dp = updater.dispatcher
    dp = setup_dispatcher(dp)

    bot_info = telegram.Bot(TBOT_TOKEN).get_me()
    bot_link = f"https://t.me/" + bot_info["username"]

    print(f"Pooling of '{bot_link}' started")
    updater.start_polling()
    updater.idle()

"""
TODO: NPI para que es esto:
@task(ignore_result=True)
def process_telegram_event(update_json):
    update = telegram.Update.de_json(update_json, bot)
    dispatcher.process_update(update)
"""

# Global variable - best way I found to init Telegram bot
bot = telegram.Bot(TBOT_TOKEN)
dispatcher = setup_dispatcher(Dispatcher(bot, None, workers=0, use_context=True))
"""
TODO: NPI para que es esto:
TELEGRAM_BOT_USERNAME = bot.get_me()["username"]
"""