from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.utils.translation import gettext as _
from django.utils.text import slugify


from data.models import ContentRatingTag, Movie
from data.models import get_first_or_create_tag

from .utils import normalize_age_certificate

class Command(BaseCommand):
    help = _("""Limpia las certificaciones de edad para que saque solo la parte principal
del mismo""")

    def handle(self, *args, **options):
        for movie in Movie.objects.all():
            print(movie.title)
            for cr in movie.content_rating_systems.all():
                # print('\t - %s' % cr.name)

                clean_name = normalize_age_certificate(cr.name)

                if clean_name != cr.name:
                    search_cr = ContentRatingTag.objects.filter(name=clean_name).all()
                    # print(clean_name)
                    if search_cr.count() == 0:
                        ContentRatingTag.objects.create(name=clean_name)
                        search_cr = ContentRatingTag.objects.filter(name=clean_name).all()

                    if search_cr.count() == 0:
                        print(" - No encuentro la certificacion de edad con el nombre '%s'" % clean_name)
                    elif search_cr.count() > 1:
                        print(" - Encuentro varias certificaciones de edad con el nombre '%s'" % clean_name)
                    else:
                        if not search_cr[0] in movie.content_rating_systems.all():
                            movie.content_rating_systems.add(search_cr[0])

                        movie.content_rating_systems.remove(cr)
                        movie.save()
        for cr in ContentRatingTag.objects.all():
            movies = Movie.objects.filter(content_rating_systems=cr).all()

            if movies.count() == 0:
                print(' - Borrando "%s"...' % cr.name)
                cr.delete()
        




"""
Approved
Approved::(, adult audience)
Approved::(No. 21499)
Approved::(Suggested for Mature Audiences)
Approved::(certificate no. 13731)
Approved::(certificate no. 14125)
Approved::(certificate no. 15345)
Approved::(video rating)
G
G::(#26870)
G::(Re-Issue)
G::(TV rating)
GP
M
M/PG
M/PG::(Approved No. 21906)
M::(Approved No. 21386)
NC-17
NC-17::(Sneak Preview)
NC-17::(rating surrendered)
NC-17::(theatrical rating)
Not Rated
Not Rated::(Blu-Ray Rating)
Not Rated::(Blu-ray rating)
Not Rated::(DVD Rating)
Not Rated::(DVD rating)
Not Rated::(Digital Rating)
Not Rated::(original Streamline Pictures dub)
Not Rated::(video rating)
PG
PG-13
PG-13::(Certificate No. 37891)
PG-13::(No. 31303)
PG-13::(No. 32366)
PG-13::(No. 36763)
PG-13::(No. 37869)
PG-13::(edited for rerate after appeal)
PG-13::(extended edition)
PG-13::(on appeal)
PG-13::(special edition)
PG-13::(special extended edition)
PG::(#28661)
PG::(Approved No. 25542)
PG::(Approved No. 26137)
PG::(Approved No. 38658)
PG::(DVD Rating)
PG::(No. 27384)
PG::(No. 29171)
PG::(VHS rating)
PG::(certificate no. 2078)
PG::(certificate no. 25716)
PG::(certificate.#23094)
PG::(special edition)
Passed::(Classified and Passed by)
Passed::(National Board of Review)
Passed::(The National Board of Review)
Passed::(the National Board of Review)
R
R::(#51564)
R::(, 2020 coda version)
R::(Approved No. 36485)
R::(No. 32781)
R::(No. 33717)
R::(No. 38444)
R::(No. 39566)
R::(Ultimate Edition)
R::(Ultimate edition)
R::(certificate.#43591)
R::(collector's edition)
R::(extended edition)
R::(rating surrendered)
R::(special edition)
TV-14
TV-14::(ABC Family)
TV-14::(Cable TV rating)
TV-14::(D, L, S, V)
TV-14::(D, TV Rating.)
TV-14::(DL)
TV-14::(DL, TV Rating.)
TV-14::(DLS)
TV-14::(DLS, TV Rating.)
TV-14::(DLS, TV rating)
TV-14::(DLSV)
TV-14::(DLSV, TV Rating.)
TV-14::(DLSV, TV rating)
TV-14::(DLV)
TV-14::(DLV, TV Rating)
TV-14::(DLV, TV Rating.)
TV-14::(DLV, TV rating)
TV-14::(DV)
TV-14::(L)
TV-14::(L, V)
TV-14::(LSV)
TV-14::(LSV, TV Rating.)
TV-14::(LSV, TV rating)
TV-14::(LV)
TV-14::(LV, TV Rating.)
TV-14::(LV, TV rating)
TV-14::(Ovation)
TV-14::(SV)
TV-14::(TCM)
TV-14::(TV Rating)
TV-14::(TV rating)
TV-14::(V)
TV-14::(cable TV rating)
TV-14::(cable rating)
TV-14::(episode two)
TV-14::(new TV rating)
TV-14::(some airings)
TV-14::(video rating)
TV-G
TV-G::(Comedy Central)
TV-G::(DVD rating)
TV-G::(Disney Channel)
TV-G::(Fox Movie Channel)
TV-G::(FreeForm)
TV-G::(Nickelodeon)
TV-G::(TV Rating)
TV-G::(TV rating)
TV-G::(tv rating)
TV-MA
TV-MA::(L)
TV-MA::(L, S, V)
TV-MA::(L, TV Rating.)
TV-MA::(LS)
TV-MA::(LSV)
TV-MA::(LSV, TV Rating.)
TV-MA::(LSV, TV rating)
TV-MA::(LV)
TV-MA::(S)
TV-MA::(TV Rating)
TV-MA::(TV rating)
TV-MA::(V)
TV-MA::(cable rating)
TV-MA::(tv rating)
TV-MA::(video rating)
TV-PG
TV-PG::(ABC Family)
TV-PG::(Cartoon Network and Nickelodeon)
TV-PG::(Cartoon Network)
TV-PG::(Cartoon Network/Nickelodeon)
TV-PG::(D, L, S, V)
TV-PG::(DL, TV rating.)
TV-PG::(DLS)
TV-PG::(DLS, TV rating)
TV-PG::(DLSV)
TV-PG::(DLV)
TV-PG::(DLV, TV rating)
TV-PG::(DSV, TV Rating.)
TV-PG::(DV)
TV-PG::(DVD rating)
TV-PG::(Disney Channel)
TV-PG::(LS, TV Rating.)
TV-PG::(LSV)
TV-PG::(LSV, TV Rating.)
TV-PG::(LV)
TV-PG::(LV, TV Rating.)
TV-PG::(LV, TV rating)
TV-PG::(Most airings)
TV-PG::(Some airings)
TV-PG::(TV Rating)
TV-PG::(TV rating)
TV-PG::(V)
TV-PG::(V, TV Rating.)
TV-PG::(V, TV rating)
TV-PG::(VHS and DVD rating)
TV-PG::(cable rating)
TV-PG::(edited)
TV-PG::(episode one)
TV-PG::(new rating)
TV-PG::(some airings)
TV-PG::(tv rating)
TV-PG::(video rating)
TV-Y
TV-Y7
TV-Y7-FV::(Fox Movie Channel and Universal Kids)
TV-Y7-FV::(Fox Movie Channel)
TV-Y7::(Disney Channel)
TV-Y7::(Nickelodeon)
TV-Y7::(Some airings)
Unrated
Unrated::(DVD rating)
Unrated::(certificate # 20425)
Unrated::(certificate #*1814*)
Unrated::(unrated extended edition)
Unrated::(video rating)
X
X::(rating surrendered)
"""