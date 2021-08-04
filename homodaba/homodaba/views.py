from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import redirect, render

from data.models import Movie, MovieStorageType, MoviePerson, get_last_items
from data.models import UserTag, get_or_create_user_tag

@login_required
def home(request):
    last_movies = get_last_items(Movie)
    last_storage_types = get_last_items(MovieStorageType)

    # Hacemos una mezcla con las ultimas pelis y 
    # las ultimas pelis de los ultimos medios
    for st in last_storage_types:
        if not st.movie in last_movies:
            last_movies.append(st.movie)

    return render(request, 'home.html', context={
        'last_movies': last_movies
    })

@login_required
def search_movies(request):
    return render(request, 'search_movies.html')

@login_required
def user_later_movies(request):
    tag = get_or_create_user_tag(request.user, UserTag.LATER_TAG)
    later_movies = Movie.objects.filter(user_tags=tag).all()

    return render(request, 'later_movies.html', context={
        'later_movies': later_movies,
    })

@login_required
def json_switch_later_tag(request, movie_id):
    movie = Movie.objects.get(id=movie_id)
    tag = get_or_create_user_tag(request.user, UserTag.LATER_TAG)
    
    insert_tag = True
    for t in movie.user_tags.all():
        if t.name == tag.name:
            insert_tag = False
    
    if insert_tag:
        movie.user_tags.add(tag)
    else:
        movie.user_tags.remove(tag)
    
    movie.save()

    return JsonResponse({"STATUS": "OK"})
