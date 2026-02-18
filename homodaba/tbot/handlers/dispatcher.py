"""
    Telegram event handlers
"""
import asyncio

import telegram
from telegram import Update
from telegram.ext import (
    Updater,
    MessageHandler,
    InlineQueryHandler, CallbackQueryHandler,
    ChosenInlineResultHandler,
    ApplicationBuilder, CommandHandler, ContextTypes, filters
)

from homodaba.settings import TBOT_TOKEN

from .commands import start_command, search_command, movie_detail_command, help_command

def setup_dispatcher(app: ApplicationBuilder):
    """
    Adding handlers for events from Telegram
    """
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("search", search_command))
    app.add_handler(CommandHandler("movie", movie_detail_command))
    app.add_handler(CommandHandler("help", help_command))

    # on noncommand i.e message - echo the message on Telegram
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_command))


async def init_bot():
    """ Run bot in pooling mode """
    app = ApplicationBuilder().token(TBOT_TOKEN).build()

    setup_dispatcher(app)

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

