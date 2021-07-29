from django.core.management.base import BaseCommand
from django.utils.translation import gettext as _

from data.models import TitleAka

class Command(BaseCommand):
    help = _("""Busca inconsistencias de la base de datos""")

    def handle(self, *args, **options):
        # Buscamos title duplicados en TitleAka
        title_akas = []
        title_akas_lower = []
        for ta in TitleAka.objects.all():
            if ta.title in title_akas:
                print(" * Encontramos un titulo duplicado exacto '%s'" % ta.title)
            else:
                if ta.title.lower() in title_akas_lower:
                    print(" * Encontramos un titulo duplicado case insensitive en '%s'" % ta.title)
                else:
                    title_akas_lower.append(ta.title.lower())
                title_akas.append(ta.title)