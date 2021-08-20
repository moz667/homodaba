from django.urls import path, include

from . import views

# Namespace de la app https://docs.djangoproject.com/en/3.0/intro/tutorial03/#namespacing-url-names
app_name = 'kodi'

urlpatterns = [
    path('json/hosts', views.json_get_kodi_hosts, name='json_get_kodi_hosts'),
    path('json/play', views.json_kodi_play, name='json_kodi_play'),
    path('json/tags', views.json_tags, name='json_tags'),
    path('json/movie/search', views.json_movie_search, name='json_movie_search'),
    path('json/movie/last', views.json_movie_last, name='json_movie_last'),
]

""" 
TODO: scraper... ya veremos
path('scraper/search', views.scraper_search, name='scraper_search'),
path('scraper/detail', views.scraper_detail, name='scraper_detail'),
"""