#!/usr/bin/env python
import os, django

def main():
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
    init_bot()

if __name__ == '__main__':
    main()
