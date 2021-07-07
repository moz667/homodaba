from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import gettext as _

from data.models import Movie

class Command(BaseCommand):
    help = _("""Borra los datos de peliculas""")

    def handle(self, *args, **options):
        Movie.objects.all().delete()
