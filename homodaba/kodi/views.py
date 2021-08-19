from distutils.util import strtobool
import json
import re
import requests

from django.contrib.auth.decorators import login_required
from django.http import Http404, JsonResponse
from django.shortcuts import render

from .models import KodiHost
from .decorators import json_basic_auth

from data.models import Tag, Movie, MovieStorageType, get_last_items
from data.search import populate_search_filter

def populate_data(data, movies, request):
    share_protocol = 'SMB'
    if 'protocol' in request.GET.keys() and request.GET["protocol"] in ["SMB", "HTTP"]:
        share_protocol = request.GET["protocol"]

    for movie in movies:
        alt_titles = movie.get_other_main_titles()
        
        for st in movie.get_storage_types():
            if st.is_net_share():
                file_url = st.get_url_to_storage_type() if share_protocol == 'HTTP' else st.path

                if file_url:
                    genre = [g.name for g in movie.genres.all()]
                    country = [g.name for g in movie.countries.all()]
                    casting = [g.name for g in movie.actors.all()]
                    director = [g.name for g in movie.directors.all()]
                    # OJO: mpaa es string, no list
                    mpaa = None
                    for g in movie.content_rating_systems.all():
                        mpaa = g.name 
                    
                    writer = [g.name for g in movie.writers.all()]
                    tag = [g.name for g in movie.tags.all()]
                    
                    data["results"].append({
                        "genre": genre,
                        "country": country,
                        "year": movie.year,
                        "rating": movie.rating if movie.rating else 0,
                        "cast": casting,
                        "director": director,
                        "mpaa": mpaa,
                        "plot": movie.get_plot(),
                        "title": movie.get_the_main_title(),
                        "originaltitle": alt_titles[0] if len(alt_titles) else '',
                        "writer": writer,
                        "tag": tag,
                        "imdbnumber": movie.get_formated_imdb_id(),
                        "file": file_url,
                        "thumb": movie.clean_poster_thumbnail_url(),
                        "poster": movie.clean_poster_url(),
                    })

"""
https://codedocs.xyz/xbmc/xbmc/group__python__xbmcgui__listitem.html#ga0b71166869bda87ad744942888fb5f14

Info label	Description

showlink	string (Battlestar Galactica) or list of strings (["Battlestar Galactica", "Caprica"])
castandrole	list of tuples ([("Michael C. Hall","Dexter"),("Jennifer Carpenter","Debra")])
sorttitle	string (Big Fan)
duration	integer (245) - duration in seconds
studio	string (Warner Bros.) or list of strings (["Warner Bros.", "Disney", "Paramount"])
tagline	string (An awesome movie) - short description of movie
set	string (Batman Collection) - name of the collection
setoverview	string (All Batman movies) - overview of the collection

code	string (101) - Production code
aired	string (2008-12-07)
credits	string (Andy Kaufman) or list of strings (["Dagur Kari", "Quentin Tarantino", "Chrstopher Nolan"]) - writing credits
lastplayed	string (Y-m-d h:m:s = 2009-04-05 23:16:04)
album	string (The Joshua Tree)
artist	list (['U2'])
votes	string (12345 votes)
path	string (/home/user/movie.avi)
trailer	string (/home/user/trailer.avi)
dateadded	string (Y-m-d h:m:s = 2009-04-05 23:16:04)
mediatype	string - "video", "movie", "tvshow", "season", "episode" or "musicvideo"
dbid	integer (23) - Only add this for items which are part of the local db. You also need to set the correct 'mediatype'!


"""

@json_basic_auth
def json_movie_last(request):
    data = {
        "results": [],
    }

    last_storage_types = get_last_items(MovieStorageType, num_items=100)

    last_movies = []
    
    for st in last_storage_types:
        if not st.movie in last_movies:
            last_movies.append(st.movie)

    populate_data(
        data, 
        last_movies, 
        request=request
    )
    
    return JsonResponse(data)

@json_basic_auth
def json_movie_search(request):
    data = {
        "results": [],
    }

    tag = None
    if 'tag' in request.GET.keys():
        for t in Tag.objects.filter(name=request.GET['tag']).all():
            tag = t

    if 'query' in request.GET.keys():
        search_movies, use_distinct = populate_search_filter(
            Movie.objects, 
            search_term=request.GET['query'],
            tag=tag.id if tag else None,
            use_use_distinct=True
        )

        populate_data(
            data, 
            search_movies.all(), 
            request=request
        )
    elif tag:
        populate_data(
            data, 
            Movie.objects.filter(tags__pk=tag.id).all(), 
            request=request
        )

    return JsonResponse(data)

@json_basic_auth
def json_tags(request):
    data = {
        "tags": [],
    }

    for tag in Tag.objects.filter().all():
        data["tags"].append(tag.name)

    return JsonResponse(data)

@login_required
def json_kodi_play(request):
    host_id = request.GET["host_id"] if "host_id" in request.GET.keys() else None
    storage_path = request.GET["storage_path"] if "storage_path" in request.GET.keys() else None

    kodi_host = None

    for k in KodiHost.objects.filter(id=host_id, owner=request.user).all():
        kodi_host = k
    
    if kodi_host:
        payload = json.dumps({ 
            "id": 1, 
            "jsonrpc": "2.0", 
            "method": "Player.Open", 
            "params": {
                "item": {
                    "file": storage_path
                }
            }
        })

        headers = {'content-type': "application/json", 'cache-control': "no-cache"}

        try:
            response = requests.request(
                "POST", kodi_host.get_json_rpc_url(), 
                data=payload, 
                headers=headers, 
                auth=(kodi_host.login_username, kodi_host.login_password)
            )

            return JsonResponse(json.loads(response.text))
        except Exception as e:
            print("Error al conectar con el servidor kodi.")
            print(e)

    raise Http404('No encontramos el servidor kodi.')

@login_required
def json_get_kodi_hosts(request):
    data = {
        "kodi_hosts": [],
    }

    for kodi_host in KodiHost.objects.filter(owner=request.user).all():
        data["kodi_hosts"].append({
            "id": kodi_host.id,
            "name": kodi_host.host_name,
            # "url": kodi_host.host_url, # No hace falta
            # "jsonrpc_url": kodi_host.get_json_rpc_url(), # Problema con CORS
            # "username": kodi_host.login_username, # No hace falta
            # "password": kodi_host.login_password, # No hace falta
        })

    return JsonResponse(data)

"""
TODO: scraper... ya veremos
def scraper_search(request):
    if len(request.GET.keys()):
        for k in request.GET.keys():
            print("%s='%s'" % (k, request.GET[k]))
    return render(request, 'kodi/scraper_search.html', {"foo": "bar"}, content_type="application/xhtml+xml")

def scraper_detail(request):
    if len(request.GET.keys()):
        for k in request.GET.keys():
            print("%s='%s'" % (k, request.GET[k]))
    return render(request, 'kodi/scraper_detail.html', {"foo": "bar"}, content_type="application/xhtml+xml")
"""