from admin_auto_filters.views import AutocompleteJsonView

from django.shortcuts import render

from .models import Person

"""
TODO: Borrar... no se esta usando

from .models import MoviePerson

class MoviePersonDirectorJsonView(AutocompleteJsonView):
    def get_queryset(self):
        return MoviePerson.objects.filter(
            role=MoviePerson.RT_DIRECTOR
        ).order_by('person__name').all()
"""

class PersonDirectorJsonView(AutocompleteJsonView):
    def get_queryset(self):
        return Person.objects.filter(
            name__icontains=self.term, is_director=True
        ).order_by('name').all()
