from django.db.models import Q
import re

from .models import Movie, TitleAka

from homodaba.settings import ELASTICSEARCH_DSL

if ELASTICSEARCH_DSL:
    from .documents import MovieDocument
    from elasticsearch_dsl import Q as DSL_Q

    def populate_search_filter_dsl(queryset, search_term, use_use_distinct=False, genre=None, content_rating_system=None):
        order_by_fields = queryset.query.order_by if queryset and queryset.query and queryset.query.order_by else None
        # TODO: stats de la busqueda (total encontrados para la paginacion) 
        # TODO: paginacion
        # TODO: No busca por tags, content_rating_systems, genres, title_akas
        # seguramente funcionaria con el prepare.... pero deberia funcionar con NextedField
        # https://elasticsearch-dsl.readthedocs.io/en/stable/search_dsl.html#the-search-object

        use_distinct = False
        # DSL_Q("multi_match", query='python django', fields=['title', 'body'])
        # OJO: se puede paginar con [x:y]
        s = MovieDocument.search().query(DSL_Q("multi_match", query=search_term))[:100]
        
        queryset = s.to_queryset()
        
        # Si el order_by es solo el campo -pk... entonces se trata del orde por defecto
        # asi que pasamos de el...
        if order_by_fields and (len(order_by_fields) > 1 or not '-pk' in order_by_fields):
            queryset = queryset.order_by(*order_by_fields)
        
        if use_use_distinct:
            return queryset.distinct() if use_distinct else queryset, use_distinct
        else:
            return queryset.distinct() if use_distinct else queryset

def populate_search_filter_model(queryset, search_term, use_use_distinct=False):
    # TODO: por ahora solo para un termino... pero en un futuro deberiamos hacerlo
    # para varios
    contains_quote = False

    year_str = None

    if search_term.find('(') > 0 and search_term.find(')') > 0:
        year_str = re.compile('.*\(|\)').sub('', search_term)
        search_term = re.compile(' \(.*').sub('', search_term).strip()

    if search_term.startswith('"'):
        contains_quote = True
        search_term = search_term[1:]
    if search_term.endswith('"'):
        contains_quote = True
        search_term = search_term[:-1]

    if not contains_quote:
        query_title = Q(title__icontains=search_term)
    else:
        query_title = Q(title__iexact=search_term)
        query_title.add(Q(title__icontains=' ' + search_term), Q.OR)
        query_title.add(Q(title__icontains=search_term + ' '), Q.OR)

    use_distinct = False

    if TitleAka.objects.filter(query_title).all().count() > 0:
        query_title = Q(title_akas__in=TitleAka.objects.filter(query_title))
        if not contains_quote:
            query_title.add(Q(title__icontains=search_term), Q.OR)
        else:
            query_title.add(Q(title__iexact=search_term), Q.OR)
        # query_title.add(Q(title_akas__in=TitleAka.objects.filter(query_title)), Q.OR)
        use_distinct = True

    if year_str:
        query_title_new = Q(year=int(year_str))
        query_title_new.add(query_title, Q.AND)
        query_title = query_title_new

    # TODO: Se pueden hacer mas cosas para mejorar la busqueda... 
    # buscar tags y generos... por ahora lo vamos a dejar asi

    if use_use_distinct:
        return queryset.filter(query_title).distinct() if use_distinct else queryset.filter(query_title), use_distinct
    else:
        return queryset.filter(query_title).distinct() if use_distinct else queryset.filter(query_title)

def populate_search_filter(queryset, search_term, use_use_distinct=False, genre=None, content_rating_system=None):
    if ELASTICSEARCH_DSL:
        return populate_search_filter_dsl(queryset, search_term, use_use_distinct=use_use_distinct, genre=genre, content_rating_system=content_rating_system)

    return populate_search_filter_model(queryset, search_term, use_use_distinct)

def movie_search_filter(search_term):
    return populate_search_filter(Movie.objects, search_term)