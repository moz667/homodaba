from django.contrib import admin
from django.db.models import Q

from .models import Movie, Person, MovieStorageType, MoviePerson, Tag, GenreTag, TitleAka

# from easy_select2 import select2_modelform
# MovieForm = select2_modelform(Movie, attrs={'width': '250px'})

class TagAdmin(admin.ModelAdmin):
    pass
admin.site.register(Tag, TagAdmin)

class GenreTagAdmin(admin.ModelAdmin):
    pass
admin.site.register(GenreTag, GenreTagAdmin)

class TitleAkaAdmin(admin.ModelAdmin):
    pass
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


class MovieAdmin(admin.ModelAdmin):
    list_display = ('title', 'year', 'get_poster_thumbnail_img', 'get_other_titles', 'rating',)
    
    # TODO: Pensar que hacemos con title_akas
    exclude = ('title_akas',)
    list_filter = (TagListFilter, GenreListFilter,)

    # Lo ponemos para que saque la caja de texto pero la busqueda
    # la hacemos manualmente en get_search_results
    search_fields = ('title',)

    def get_search_results(self, request, queryset, search_term):
        # Si No hay terminos de busqueda devolvemos el queryset tal como esta
        if not search_term:
            return queryset, False
        
        # super:
        # No lo usamos porque no nos deja agregar como opcion el title_akas__in
        # queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        akas_queryset = TitleAka.objects.filter(title__icontains=search_term)
        query_title = Q(title__icontains=search_term)
        use_distinct = False

        if akas_queryset.count() > 0:
            query_title.add(Q(title_akas__in=TitleAka.objects.filter(title__icontains=search_term)), Q.OR)
            use_distinct = True

        # Para mejorar la busqueda podemos hacer que si el search_term se trata de un numero entero de 4 cifras
        # podria tratarse del año de producion
        if search_term and len(search_term) == 4 and search_term >= '1000' and search_term <= '9999':
            query_title.add(Q(year=int(search_term)), Q.OR)

        # TODO: Se pueden hacer mas cosas para mejorar la busqueda... 
        # buscar tags y generos... por ahora lo vamos a dejar asi :P

        queryset = queryset.filter(query_title)

        return queryset, use_distinct

    # form = MovieForm
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
