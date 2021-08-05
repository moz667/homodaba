from admin_auto_filters.views import AutocompleteJsonView

from django.shortcuts import render

from .models import Person

class PersonDirectorJsonView(AutocompleteJsonView):
    def get_queryset(self):
        return Person.objects.filter(
            name__icontains=self.term, is_director=True
        ).order_by('name').all()
