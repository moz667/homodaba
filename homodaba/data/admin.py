from django.contrib import admin

# Register your models here.

from .models import *

class MovieAdmin(admin.ModelAdmin):
    list_display = ('year', 'title', 'title_original', 'title_preferred', 'imdb_id')
    """
    TODO: Pensar que hacemos con estos...
    title_akas
    tags
    genres
    """
    exclude = ('title_akas', 'tags', 'genres')
admin.site.register(Movie, MovieAdmin)

class PersonAdmin(admin.ModelAdmin):
    list_display = ('name', 'imdb_id', 'avatar_url')
admin.site.register(Person, PersonAdmin)

class MovieStorageTypeAdmin(admin.ModelAdmin):
    list_display = ('get_movie_title', 'is_original', 'storage_type', 'media_format', 'resolution')
    list_filter = ('storage_type', 'media_format', )
    def get_movie_title(self, obj):
        return obj.movie.title
    get_movie_title.short_description = 'Pelicula'
    get_movie_title.admin_order_field = 'movie__title'
admin.site.register(MovieStorageType, MovieStorageTypeAdmin)

class MoviePersonAdmin(admin.ModelAdmin):
    list_display = ('get_movie_title', 'get_movie_year', 'get_person_name', 'role')
    list_filter = ('role', )

    def get_movie_title(self, obj):
        return obj.movie.title
    get_movie_title.short_description = 'Pelicula'
    get_movie_title.admin_order_field = 'movie__title'

    def get_movie_year(self, obj):
        return obj.movie.year
    get_movie_year.short_description = 'Año'
    get_movie_year.admin_order_field = 'movie__year'

    def get_person_name(self, obj):
        return obj.person.name
    get_person_name.short_description = 'Participante'
    get_person_name.admin_order_field = 'person__name'

admin.site.register(MoviePerson, MoviePersonAdmin)
