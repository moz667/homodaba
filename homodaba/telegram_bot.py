#!/usr/bin/env python
import asyncio
import os, django

async def main():
    # Init app django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homodaba.settings')
    django.setup()

    try:
        from tbot.handlers.dispatcher import init_bot
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    await init_bot()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except RuntimeError:
        # Evita el error visual de loop cerrado al final en algunos SO
        pass
