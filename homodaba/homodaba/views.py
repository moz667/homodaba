from distutils.util import strtobool
import re

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import redirect, render

from data.models import Movie, MovieStorageType, Person, get_last_items
from data.models import UserTag, get_or_create_user_tag
from data.models import Tag, GenreTag, ContentRatingTag
from data.search import populate_search_filter

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
    director = get_person_filter(request, 'director', is_director=True)
    writer = get_person_filter(request, 'writer', is_writer=True)
    actor = get_person_filter(request, 'actor', is_actor=True)

    unseen = strtobool(request.GET['unseen']) if 'unseen' in request.GET.keys() and request.GET['unseen'] else None
    seen_tag = get_or_create_user_tag(request.user, UserTag.SEEN_TAG)

    tag = get_tag_filter(request, 'tag', Tag)
    genre = get_tag_filter(request, 'genre', GenreTag)
    cr_system = get_tag_filter(request, 'cr_system', ContentRatingTag)
    user_tag = get_tag_filter(request, 'user_tag', UserTag)

    search_term = request.GET['search_term'] if 'search_term' in request.GET.keys() else ''

    search_movies, use_distinct = populate_search_filter(
        Movie.objects, 
        search_term=search_term,
        director=director.id if director else None,
        writer=writer.id if writer else None,
        actor=actor.id if actor else None,
        tag=tag.id if tag else None,
        genre=genre.id if genre else None,
        content_rating_system=cr_system.id if cr_system else None,
        user_tag=user_tag.id if user_tag else None,
        unseen=unseen,
        seen_tag=seen_tag.id,
        use_use_distinct=True
    )

    order_by = ['-id']
    if 'order_by' in request.GET.keys() and request.GET['order_by']:
        order_by = (request.GET['order_by'], )

        if not order_by[0] in ['id', '-id']:
            order_by = (order_by[0], 'id')

    paginator = Paginator(search_movies.all().order_by(*order_by), per_page=12)

    current_page = 1
    if 'page' in request.GET.keys():
        current_page = int(request.GET['page'])

    return render(request, 'search_movies.html',context={
        'search_movies': paginator.get_page(current_page).object_list,
        'search_term': search_term,
        'order_by': request.GET['order_by'] if 'order_by' in request.GET.keys() else '',
        'current_page': current_page,
        'next_page': current_page + 1 if paginator.num_pages > current_page else None,
        'paginator': paginator,
        'filters': {
            'director': director.name if director else '',
            'director_query': (director.name if director else '') + 
                (" [%s]" % director.imdb_id if director and director.imdb_id else ''),
            'writer': writer.name if writer else '',
            'writer_query': (writer.name if writer else '') + 
                (" [%s]" % writer.imdb_id if writer and writer.imdb_id else ''),
            'actor': actor.name if actor else '',
            'actor_query': (actor.name if actor else '') + 
                (" [%s]" % actor.imdb_id if actor and actor.imdb_id else ''),
            'tag': tag.name if tag else '',
            'genre': genre.name if genre else '',
            'cr_system': cr_system.name if cr_system else '',
            'user_tag': user_tag.name if user_tag else '',
            'unseen': unseen or '',
        }
    })

def get_tag_filter(request, request_key, class_tag):
    tag_filter = None
    if request_key in request.GET.keys():
        if request.GET[request_key]:
            tags = class_tag.objects.filter(name=request.GET[request_key]).all()
            if tags.count() > 0:
                tag_filter = tags[0]
    
    return tag_filter

def get_person_filter(request, request_key, **kargs):
    person_filter = None
    if request_key in request.GET.keys():
        if request.GET[request_key]:
            imdb_id = None
            pattern = re.compile(".*\[([0-9]+)\]")
            person_name = request.GET[request_key]

            if pattern.search(person_name):
                imdb_id = pattern.search(person_name).groups()[0]
                person_name = person_name.replace("[%s]" % imdb_id, "").strip()

            persons = []
            if imdb_id:
                persons = Person.objects.filter(name=person_name, imdb_id=imdb_id, **kargs).all()
            else:
                persons = Person.objects.filter(name=person_name, **kargs).all()

            if persons.count() > 0:
                person_filter = persons[0]
    
    return person_filter


@login_required
def user_later_movies(request):
    tag = get_or_create_user_tag(request.user, UserTag.LATER_TAG)
    later_movies = Movie.objects.filter(user_tags=tag).all()

    return render(request, 'later_movies.html', context={
        'later_movies': later_movies,
    })

@login_required
def json_switch_user_tag(request, tag_type, movie_id):
    movie = Movie.objects.get(id=movie_id)
    tag = get_or_create_user_tag(request.user, tag_type)
    
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
