from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.utils.translation import gettext as _

from data.models import Movie, Person, MovieStorageType, MoviePerson

import csv
from datetime import datetime
import os
import sys
from time import sleep

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

class Command(BaseCommand):
    help = _('Arranca el bot the telegram')

    def add_arguments(self, parser):
        parser.add_argument('--token', nargs='+', type=str, help="""Token de la API de telegram, https://core.telegram.org/bots#6-botfather""")
    
    def search_movie_local_data(self, title, year):
        query_title = Q(title__iexact=title)
        query_title.add(Q(title_original__iexact=title), Q.OR)
        query_title.add(Q(title_preferred__iexact=title), Q.OR)

        query = Q(query_title)
        query_title.add(Q(year=year), Q.AND)
        
        return Movie.objects.filter(query).all()

    def handle(self, *args, **options):
        if not 'token' in options or not options['token'] or not options['token'][0]:
            self.help()
            return
        

