from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import redirect, render

from data.models import Movie, MovieStorageType, MoviePerson, get_last_five

@login_required
def home(request):
    last_movies = get_last_five(Movie)
    last_storage_types = get_last_five(MovieStorageType)
    return render(request, 'home.html', context={
        'last_movies': last_movies,
        'last_storage_types': last_storage_types,
    })

@login_required
def search_movies(request):
    return render(request, 'search_movies.html')

@login_required
def search_movies_by_director(request, id):
    return render(request, 'search_movies.html')
