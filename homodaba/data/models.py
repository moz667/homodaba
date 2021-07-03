from django.db import models
from django.db.models import Q
from django.utils.html import format_html
from django.utils.safestring import mark_safe

class Person(models.Model):
    name = models.CharField('Nombre', max_length=200, null=False, blank=False)
    canonical_name = models.CharField('Nombre (Canónico)', max_length=200, null=False, blank=False)
    imdb_id = models.CharField('IMDB ID', max_length=20, null=True, blank=True)
    avatar_url = models.CharField('Foto (URL)', max_length=255, null=True, blank=True)
    avatar_thumbnail_url = models.CharField('Foto en miniatura (URL)', max_length=255, null=True, blank=True)
    is_director = models.BooleanField('Director', default=False, null=False, blank=False)
    is_writer = models.BooleanField('Escritor', default=False, null=False, blank=False)
    is_actor = models.BooleanField('Actor', default=False, null=False, blank=False)
    is_scraped = models.BooleanField('Scrapeado', default=False, null=False, blank=False)
    imdb_raw_data = models.TextField('RAW DATA IMDB', null=True, blank=True)

    # TODO: Borrar... no se esta usando
    # movies_as_director = models.ManyToManyField('Movie', through='MoviePersonDirectorProxy')

    def get_imdb_url(self):
        if self.imdb_id:
            return 'https://www.imdb.com/name/nm%s/' % self.imdb_id
        
        return None

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "persona"
        verbose_name_plural = "personas"

class AbstractTag(models.Model):
    name = models.CharField(max_length=100, unique=True)
    
    def __str__(self):
        return self.name

    class Meta:
        abstract = True

class Tag(AbstractTag):
    class Meta:
        verbose_name = "etiqueta"
        verbose_name_plural = "etiquetas"

class GenreTag(AbstractTag):
    class Meta:
        verbose_name = "género"
        verbose_name_plural = "géneros"

# https://en.wikipedia.org/wiki/Motion_Picture_Association_film_rating_system
# https://en.wikipedia.org/wiki/TV_Parental_Guidelines
class ContentRatingTag(AbstractTag):
    class Meta:
        verbose_name = "clasificación de edad"
        verbose_name_plural = "clasificaciones de edad"

class TitleAka(models.Model):
    title = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "título conocido (aka)"
        verbose_name_plural = "títulos conocidos (akas)"

class Movie(models.Model):
    MK_MOVIE = 'movie'
    MK_SERIE = 'tv series'

    MOVIE_KINDS = [
        (MK_MOVIE, 'Película'),
        (MK_SERIE, 'Serie de television'),
    ]

    title = models.CharField('Título (Internacional)', max_length=200, 
        null=False, blank=False)
    title_original = models.CharField('Título (Original)', max_length=200, 
        null=True, blank=True)
    title_preferred = models.CharField('Título (Idioma preferido)', 
        max_length=200, null=True, blank=True)
    imdb_id = models.CharField('IMDB ID', max_length=20, null=True, blank=True)
    kind = models.CharField('Clase de pélicula', max_length=20, 
        choices=MOVIE_KINDS, default=MK_MOVIE, null=False, blank=False)
    summary = models.TextField('Resumen', null=True, blank=True)
    poster_url = models.CharField('Cartel (URL)', max_length=255, null=True, 
        blank=True)
    poster_thumbnail_url = models.CharField('Cartel en miniatura (URL)', 
        max_length=255, null=True, blank=True)
    year = models.IntegerField('Año', null=True, blank=True)
    rating = models.DecimalField('Puntuación', null=True, blank=True, 
        max_digits=4, decimal_places=2)
    # TODO: oops... esta relacion deberia ser one2many VVVV
    title_akas = models.ManyToManyField(TitleAka)
    # TODO: oops... esta relacion deberia ser one2many ^^^^
    tags = models.ManyToManyField(Tag)
    genres = models.ManyToManyField(GenreTag)
    content_rating_systems = models.ManyToManyField(ContentRatingTag)

    # Esto tiene miga... para mantener la relacion m2m a Person a traves de 
    # MoviePerson, por ser un modelo a medida, se tiene que hacer a traves
    # del proxy: MoviePersonDirectorProxy
    directors = models.ManyToManyField(Person, through='MoviePersonDirectorProxy')

    is_scraped = models.BooleanField('Scrapeado', default=False, null=False, 
        blank=False)
    imdb_raw_data = models.TextField('RAW data IMDB', null=True, blank=True)
    
    def __str__(self):
        return self.title

    def get_complete_title(self):
        return '%s (%s)' % (self.title, str(self.year))

    def get_other_titles(self):
        other_titles = []
        if self.title_original and self.title_original != self.title:
            other_titles.append(self.title_original)
        if self.title_preferred and self.title_preferred != self.title:
            other_titles.append(self.title_preferred)
        for ta in self.title_akas.all():
            other_titles.append(ta.title)

        return ', '.join(other_titles)
    get_other_titles.short_description = 'Otros títulos'

    def get_directed_by(self):
        directed_by = []
        for d in self.get_directors():
            directed_by.append(d.name)
        
        return ', '.join(directed_by)
    get_directed_by.short_description = 'Dirigida por'

    def get_persons(self, role=None):
        query = Q(movie=self)
        if role:
            query.add(Q(role=role), Q.AND)
        mmpp = MoviePerson.objects.filter(query).all()
        persons = []
        for mp in mmpp:
            persons.append(mp.person)
        return persons
    
    def get_directors(self):
        return self.get_persons(MoviePerson.RT_DIRECTOR)
    
    def get_writers(self):
        return self.get_persons(MoviePerson.RT_WRITER)

    def get_actors(self):
        return self.get_persons(MoviePerson.RT_ACTOR)

    def get_poster_thumbnail_img(self):
        return format_html(
            '<a href="{}" target="_blank" class="modal-photo"><img src="{}" alt="{}" /></a>',
            'https://www.imdb.com/title/tt%s/' % self.imdb_id if self.imdb_id else 'https://www.imdb.com/title/tt0385307/',
            self.poster_thumbnail_url if self.poster_thumbnail_url else 'https://m.media-amazon.com/images/M/MV5BMjAxNzk2OTI2OV5BMl5BanBnXkFtZTcwODk0MDIzMw@@._V1_SY150_CR0,0,101,150_.jpg',
            self.title,
        )
    get_poster_thumbnail_img.short_description = 'Cartel'

    def get_storage_types_html(self):
        storage_types = MovieStorageType.objects.filter(movie=self).all()
        if storage_types.count() == 0:
            return ''

        html = '<ul class="storage-types">'
        for st in storage_types:
            html = html + format_html('<li>{}</li>', st)
        html = html + '</ul>'
        return mark_safe(html)
    get_storage_types_html.short_description = 'Medios'

    def get_storage_types_html_tg(self):
        storage_types = MovieStorageType.objects.filter(movie=self).all()
        if storage_types.count() == 0:
            return ''

        html = '<pre>'
        for st in storage_types:
            html = html + format_html('    * {}\n', st)
        html = html + '</pre>\n'
        return mark_safe(html)
    get_storage_types_html_tg.short_description = 'Medios (para telegram)'
    
    def get_storage_types_text(self):
        storage_types = MovieStorageType.objects.filter(movie=self).all()
        if storage_types.count() == 0:
            return ''

        return ' * '.join([st.__str__() + '\n' for st in storage_types])

    class Meta:
        verbose_name = "película"
        verbose_name_plural = "películas"

class MoviePerson(models.Model):
    RT_DIRECTOR = 'director'
    RT_WRITER = 'writer'
    RT_ACTOR = 'actor'

    ROLE_TYPES = [
        (RT_DIRECTOR, 'Director'),
        (RT_WRITER, 'Guionista'),
        (RT_ACTOR, 'Actor/Actriz'),
    ]

    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, verbose_name='pelicula')
    person = models.ForeignKey(Person, on_delete=models.CASCADE, verbose_name='participante')
    role = models.CharField('Rol', max_length=20, choices=ROLE_TYPES, default=RT_DIRECTOR, null=False, blank=False)

    def __str__(self):
        return '%s -> %s' % (self.movie.get_complete_title(), self.person)

    class Meta:
        verbose_name = 'reparto'
        verbose_name_plural = 'repartos'

# Manager y Proxy para las relaciones que se pudieran sacar
# de directores solo (role=MoviePerson.RT_DIRECTOR), esto se hace
# para simplificar este tipo de relaciones (ahora mismo se esta usando
# para sacar directors en Movie)
class MoviePersonDirectorManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(role=MoviePerson.RT_DIRECTOR)

class MoviePersonDirectorProxy(MoviePerson):
    class Meta:
        proxy = True
    
    objects = MoviePersonDirectorManager()
# ^^^^^^^^^^^^

class MovieStorageType(models.Model):
    ST_DRIVE = 'hard-drive'
    ST_NEW_SHARE = 'net-share'
    ST_DVD = 'dvd'
    ST_BRAY = 'bluray'
    ST_ULTRA_BRAY = 'ultra-bluray'
    ST_VHS = 'vhs'

    STORAGE_TYPES = [
        (ST_DRIVE, 'Disco duro'),
        (ST_NEW_SHARE, 'Compartido de red'),
        (ST_DVD, 'DVD'),
        (ST_BRAY, 'BLURAY'),
        (ST_ULTRA_BRAY, 'ULTRA BLURAY'),
        (ST_VHS, 'VHS'),
    ]

    STORAGE_TYPES_AS_LIST = [k for (k, v) in STORAGE_TYPES]
    STORAGE_TYPES_AS_DICT = {k:v for (k, v) in STORAGE_TYPES}

    MF_AVI = 'AVI'
    MF_BLURAY = 'BLURAY'
    MF_BLURAY_ISO = 'BLURAY-ISO'
    MF_DVD = 'DVD'
    MF_DVD_ISO = 'DVD-ISO'
    MF_ISO = 'ISO'
    MF_M2TS = 'M2TS'
    MF_M4V = 'M4V'
    MF_MKV = 'MKV'
    MF_MP4 = 'MP4'
    MF_ULTRA_BRAY = 'ULTRA-BLURAY'

    MEDIA_FORMATS = [
        (MF_AVI, MF_AVI),
        (MF_BLURAY, MF_BLURAY),
        (MF_BLURAY_ISO, MF_BLURAY_ISO),
        (MF_DVD, MF_DVD),
        (MF_DVD_ISO, MF_DVD_ISO),
        (MF_ISO, MF_ISO),
        (MF_M2TS, MF_M2TS),
        (MF_M4V, MF_M4V),
        (MF_MKV, MF_MKV),
        (MF_MP4, MF_MP4),
        (MF_ULTRA_BRAY, MF_ULTRA_BRAY),
    ]

    MEDIA_FORMATS_AS_LIST = [k for (k, v) in MEDIA_FORMATS]

    MEDIA_FORMATS_FILE_WITH_OTHER_EXTENSION = [
        MF_AVI, MF_M2TS, MF_M4V, MF_MKV, MF_MP4
    ]

    MEDIA_FORMATS_FILE_WITH_ISO_EXTENSION = [
        MF_BLURAY_ISO, MF_DVD_ISO, MF_ISO
    ]

    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, verbose_name='pelicula')
    is_original = models.BooleanField('Original', default=True, null=False, blank=False)
    storage_type = models.CharField('Tipo de almacenamiento', max_length=20, choices=STORAGE_TYPES, default=ST_DVD, null=False, blank=False)
    name = models.CharField('Nombre del almacenamiento', max_length=200, null=True, blank=True)
    path = models.CharField('Ubicación', max_length=512, null=True, blank=True)
    media_format = models.CharField('Formato', max_length=20, choices=MEDIA_FORMATS, default=MF_DVD, null=False, blank=False)
    resolution = models.CharField('Resolución', max_length=20, null=True, blank=True)
    version = models.CharField('Versión', max_length=512, null=True, blank=True)

    def __str__(self):
        s = '(Original) ' if self.is_original else ''
        s = s + ('(%s) ' % self.version if self.version else '')
        s = s + (self.STORAGE_TYPES_AS_DICT[self.storage_type])
        s = s + (' [%s]' % self.name if self.name else '')
        s = s + (' "%s"' % self.path if self.path else '')
        s = s + (' {%s}' % self.media_format if self.media_format != self.STORAGE_TYPES_AS_DICT[self.storage_type] else '')
        return s

    class Meta:
        verbose_name = "tipo de almacenamiento"
        verbose_name_plural = "tipos de almacenamiento"

def get_first_or_create_tag(class_model, **kwargs):
    results = class_model.objects.filter(**kwargs).all()
    if results.count() > 0:
        return results[0]
    
    return class_model.objects.create(**kwargs)

