"""homodaba URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from .settings import HOME_URL_PATH

from . import views

urlpatterns = [
    path('%s' % HOME_URL_PATH, views.home, name='home'),
    path('%smovies/' % HOME_URL_PATH, views.search_movies, name='search_movies'),
    path('%smovies/later' % HOME_URL_PATH, views.user_later_movies, name='user_later_movies'),
    path(
        '%sjson/user-tag/<str:tag_type>/<int:movie_id>' % HOME_URL_PATH, 
        views.json_switch_user_tag, name='json_switch_user_tag'
    ),
    path('%sadmin/' % HOME_URL_PATH, admin.site.urls),
    path('%sauth/' % HOME_URL_PATH, include('django.contrib.auth.urls')),
    path('%si18n/' % HOME_URL_PATH, include('django.conf.urls.i18n')),
]
