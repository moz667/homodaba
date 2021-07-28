from django.core.management.base import BaseCommand
from django.utils.translation import gettext as _

from data.models import ImdbCache

import getch

class Command(BaseCommand):
    help = _("""Borra los datos de cache""")

    def handle(self, *args, **options):
        print("")
        print(" * Esta seguro que desea borrar toda la cache? [y/N]: ")
        
        selected_option = getch.getch()

        if selected_option.lower() == 'y':
            ImdbCache.objects.all().delete()
            print(" # Cache borrada #")