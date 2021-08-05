
from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry

from elasticsearch_dsl import analyzer

from .models import Movie, MoviePerson, Person

"""
Necesitamos leer la documentacion de las cosas antes de usarlas...
Elastic Search es muy extenso y no es prioritario, para empezar a usarlo con 
cabeza tenemos que entender como funciona y sus posibilidades

Info para que miremos: 
    https://www.elastic.co/guide/en/elasticsearch/reference/7.x/index.html
    https://elasticsearch-dsl.readthedocs.io/
    https://django-elasticsearch-dsl-drf.readthedocs.io/
"""

# Analizador de texto personalizado para los titulos en ingles
# Deberiamos hacer uno para spanish pero npi :P
title_simple_en_analyzer = analyzer(
    'simple', # https://www.elastic.co/guide/en/elasticsearch/reference/current/analysis-simple-analyzer.html
    tokenizer="standard", # https://www.elastic.co/guide/en/elasticsearch/reference/current/analysis-standard-tokenizer.html
    filter=[
        "lowercase", # https://www.elastic.co/guide/en/elasticsearch/reference/current/analysis-lowercase-tokenfilter.html
        # stop lo he quitado porque esto tiene mas sentido para textos largos, 
        # en el caso de los titulos, que es cuando se usa ahora, no parece 
        # indicado quitar terminos como the, to... ya que los titulos son cadenas
        # con pocas palabras
        # "stop", # https://www.elastic.co/guide/en/elasticsearch/reference/current/analysis-stop-tokenfilter.html
        "snowball" # https://www.elastic.co/guide/en/elasticsearch/reference/current/analysis-snowball-tokenfilter.html
    ]
)
@registry.register_document
class MovieDocument(Document):
    title = fields.TextField(
        analyzer=title_simple_en_analyzer,
        fields={'raw': fields.KeywordField()}
    )

    title_original = fields.TextField(
        analyzer=title_simple_en_analyzer,
        fields={'raw': fields.KeywordField()}
    )

    title_preferred = fields.TextField(
        analyzer=title_simple_en_analyzer,
        fields={'raw': fields.KeywordField()}
    )

    genres = fields.NestedField(properties={
        'name': fields.TextField(),
        'pk': fields.IntegerField(),
    })

    content_rating_systems = fields.NestedField(properties={
        'name': fields.TextField(),
        'pk': fields.IntegerField(),
    })

    tags = fields.NestedField(properties={
        'name': fields.KeywordField(),
        'pk': fields.IntegerField(),
    })

    title_akas = fields.NestedField(properties={
        'title': fields.TextField(),
        'pk': fields.IntegerField(),
    })

    # Para las personas no veo otra forma de hacerlo... VVVV 
    # TODO: Investigar. Para el nuevo filtro por director, no consegui hacerlo 
    # funcionar como ObjectField pero si funciona como NestedField... NPI!
    directors = fields.NestedField(properties={
        'name': fields.TextField(),
        'pk': fields.IntegerField(),
    })

    writers = fields.ObjectField(properties={
        'name': fields.TextField(),
        'pk': fields.IntegerField(),
    })

    casting = fields.ObjectField(properties={
        'name': fields.TextField(),
        'pk': fields.IntegerField(),
    })

    user_tags = fields.NestedField(properties={
        'name': fields.KeywordField(),
        'pk': fields.IntegerField(),
    })

    # TODO: ojo!!! esto es para que solo indexe los primeros X
    #def get_queryset(self):
    #    return super().get_queryset()[:50]

    def _prepare_persons(self, cur_persons):
        ret_persons = []

        for p in cur_persons:
            ret_persons.append({
                'pk': p.id,
                'name': p.name,
            })

        return ret_persons

    def prepare_directors(self, movie):
        return self._prepare_persons(movie.get_directors())

    def prepare_writers(self, movie):
        return self._prepare_persons(movie.get_writers())

    def prepare_casting(self, movie):
        return self._prepare_persons(movie.get_actors())
    # Para las personas no veo otra forma de hacerlo... ^^^^

    class Index:
        # Name of the Elasticsearch index
        name = 'movies'
        # See Elasticsearch Indices API reference for available settings
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0,
        }

    class Django:
        model = Movie # The model associated with this Document

        # The fields of the model you want to be indexed in Elasticsearch
        fields = [
            'imdb_id',
            'year',
            # 'summary', TODO: he quitado summary por ahora para afinar busquedas por otros campos
        ]

        # Ignore auto updating of Elasticsearch when a model is saved
        # or deleted:
        # ignore_signals = True

        # Don't perform an index refresh after every update (overrides global setting):
        # auto_refresh = False

        # Paginate the django queryset used to populate the index with the specified size
        # (by default it uses the database driver's default setting)
        # queryset_pagination = 5000

"""
@registry.register_document
class PersonDocument(Document):
    class Django:
        model = Person
        fields = [
            'name',
        ]

    class Index:
        name = "person"


@registry.register_document
class MoviePersonDocument(Document):
    person = fields.NestedField(properties={
        'name': fields.TextField(),
        'pk': fields.IntegerField(),
    })

    movie = fields.NestedField(properties={
        'title': fields.TextField(),
        'pk': fields.IntegerField(),
    })

    class Django:
        model = MoviePerson
        fields = [
            'role',
        ]

    class Index:
        name = "movie_person"
"""