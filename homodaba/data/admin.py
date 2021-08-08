from django.contrib import admin
from django.db.models import Q
from django.shortcuts import reverse
from django.urls import path

from admin_auto_filters.filters import AutocompleteFilter

from .models import Movie, Person, MovieStorageType, MoviePerson, Tag, GenreTag, TitleAka, ContentRatingTag, ImdbCache
from .search import populate_search_filter
from .views import PersonDirectorJsonView

from homodaba.settings import ELASTICSEARCH_DSL, ADMIN_MOVIE_LIST_PER_PAGE, DATABASES

# Problemilla con la relacion de Movie -> MoviePerson
class DirectorFilter(AutocompleteFilter):
    title = 'Director' # display title
    field_name = 'directors' # name of the foreign key field

    def get_autocomplete_url(self, request, model_admin):
        return reverse('admin:json_autocomplete_director_search')

class ImdbCacheAdmin(admin.ModelAdmin):
    # A handy constant for the name of the alternate database.
    using = 'cache' if 'cache' in DATABASES.keys() else 'default'

    def save_model(self, request, obj, form, change):
        # Tell Django to save objects to the 'other' database.
        obj.save(using=self.using)

    def delete_model(self, request, obj):
        # Tell Django to delete objects from the 'other' database
        obj.delete(using=self.using)

    def get_queryset(self, request):
        # Tell Django to look for objects on the 'other' database.
        return super().get_queryset(request).using(self.using)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Tell Django to populate ForeignKey widgets using a query
        # on the 'other' database.
        return super().formfield_for_foreignkey(db_field, request, using=self.using, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        # Tell Django to populate ManyToMany widgets using a query
        # on the 'other' database.
        return super().formfield_for_manytomany(db_field, request, using=self.using, **kwargs)
admin.site.register(ImdbCache, ImdbCacheAdmin)

class TagAdmin(admin.ModelAdmin):
    pass
admin.site.register(Tag, TagAdmin)

class GenreTagAdmin(admin.ModelAdmin):
    pass
admin.site.register(GenreTag, GenreTagAdmin)

class TitleAkaAdmin(admin.ModelAdmin):
    search_fields = ('title',)
admin.site.register(TitleAka, TitleAkaAdmin)

class CustomAbstractTagListFilter(admin.SimpleListFilter):
    """
    Filtro personalizado para AbstractTag
    """
    title = 'Filtro de tags personalizado'
    parameter_name = 'tag'
    tag_model = None
    tag_filter = 'tags__id'

    def lookups(self, request, model_admin):
        filters = tuple()
        for gt in self.tag_model.objects.order_by('name').all():
            filters = filters + ((gt.id, gt.name),)

        return filters
 
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(**{self.tag_filter: self.value()})
        
        return queryset
    
    class Meta:
        abstract = True

class TagListFilter(CustomAbstractTagListFilter):
    title = 'Etiquetas'
    parameter_name = 'tag'
    tag_model = Tag
    tag_filter = 'tags__id'


class GenreListFilter(CustomAbstractTagListFilter):
    title = 'Géneros'
    parameter_name = 'genre'
    tag_model = GenreTag
    tag_filter = 'genres__id'

class ContentRatingListFilter(CustomAbstractTagListFilter):
    title = 'Clasificaciones de edad'
    parameter_name = 'crs'
    tag_model = ContentRatingTag
    tag_filter = 'content_rating_systems__id'


class MovieAdmin(admin.ModelAdmin):
    list_display = ('title', 'year', 'get_poster_thumbnail_img', 'get_directed_by', 'get_main_titles_html', 'get_storage_types_html', 'rating',)
    
    # TODO: Pensar que hacemos con title_akas
    exclude = ('title_akas', 'directors', 'writers', 'actors')
    list_filter = (DirectorFilter, TagListFilter, GenreListFilter, ContentRatingListFilter)

    # Lo ponemos para que saque la caja de texto pero la busqueda
    # la hacemos manualmente en get_search_results
    search_fields = ('title', 'title_original', 'title_preferred',)

    list_per_page = ADMIN_MOVIE_LIST_PER_PAGE

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('json/autocomplete/director/search/', self.admin_site.admin_view(
                    PersonDirectorJsonView.as_view(model_admin=self)
                ),
                name='json_autocomplete_director_search'
            ),
        ]
        return custom_urls + urls

    def get_search_results(self, request, queryset, search_term):
        # Si No hay terminos de busqueda devolvemos el queryset tal como esta
        if not search_term:
            # Hace un distinct() porque las busquedas con el filtro de director
            # devolvia duplicados
            return queryset.distinct(), False

        # OJO: Esto deberia ser necesario para ElasticSearch VVVVV
        if ELASTICSEARCH_DSL:
            genre_filter = None
            if 'genre' in request.GET.keys():
                if request.GET['genre']:
                    genre_filter = int(request.GET['genre'])
            
            crs_filter = None
            if 'crs' in request.GET.keys():
                if request.GET['crs']:
                    crs_filter = int(request.GET['crs'])

            tag_filter = None
            if 'tag' in request.GET.keys():
                if request.GET['tag']:
                    tag_filter = int(request.GET['tag'])

            director_filter = None
            if 'directors__pk__exact' in request.GET.keys():
                if request.GET['directors__pk__exact']:
                    director_filter = int(request.GET['directors__pk__exact'])
            
            return populate_search_filter(queryset, search_term, use_use_distinct=True, genre=genre_filter, content_rating_system=crs_filter, tag=tag_filter, director=director_filter)
        # OJO: Esto deberia ser necesario para ElasticSearch ^^^^

        return populate_search_filter(queryset, search_term, use_use_distinct=True)

    # form = MovieForm
admin.site.register(Movie, MovieAdmin)

class PersonAdmin(admin.ModelAdmin):
    list_display = ('name', 'imdb_id', 'is_director', 'is_writer', 'is_actor', 'avatar_url')

    search_fields = ('name', 'canonical_name',)
    list_filter = ('is_director', 'is_writer', 'is_actor', )
admin.site.register(Person, PersonAdmin)

class MovieStorageTypeAdmin(admin.ModelAdmin):
    list_display = ('get_movie_title', 'is_original', 'storage_type', 'media_format', 'resolution')
    list_filter = ('storage_type', 'media_format', )

    search_fields = ('path',)

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
