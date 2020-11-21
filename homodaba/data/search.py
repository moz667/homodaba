from django.db.models import Q, Max, Min

import re
from datetime import datetime

from .models import Movie, TitleAka

from homodaba.settings import ELASTICSEARCH_DSL

if ELASTICSEARCH_DSL:
    from .documents import MovieDocument
    from elasticsearch_dsl import Q as DSL_Q

    def populate_search_filter_dsl(queryset, search_term, use_use_distinct=False, genre=None, content_rating_system=None, tag=None, year=None):
        order_by_fields = queryset.query.order_by if queryset and queryset.query and queryset.query.order_by else None
        # TODO: stats de la busqueda (total encontrados para la paginacion)
        # TODO: paginacion
        # TODO: Analizadores de terminos para permitir busquedas por texto parcial

        use_distinct = False

        query = DSL_Q('bool')

        # puede ser que busquemos solo por año, (XXXX) en ese caso no tendremos
        # mas terminos de busqueda
        if search_term:
            # Los objects se pueden consultar directamente sobre la consulta 
            # principal, como directores, escritores actores...
            query.should.append(DSL_Q("multi_match", query=search_term, 
                fields=["title^4", "directors.name^3", "writers.name^2", "casting.name^2"]
            ))

            query.should.append(DSL_Q("nested", path="title_akas", 
                query=DSL_Q("multi_match", 
                    query=search_term, fields=["title_akas.title^4"]
                )
            ))

            # Si filtramos por tag, no tiene sentido que busquemos terminos 
            # de la tag
            if tag == None:
                query.should.append(DSL_Q("nested", path="tags", 
                    query=DSL_Q("multi_match", 
                        query=search_term, fields=["tags.name^4"]
                    )
                ))
        
        # Para los nested hay que hacer una query especifica del tipo "nested"
        if tag:
            query.must.append(DSL_Q("nested", path="tags", 
                query=DSL_Q("match", tags__pk=tag)
            )) 
        
        if genre:
            query.must.append(DSL_Q("nested", path="genres", 
                query=DSL_Q("match", genres__pk=genre)
            ))
        
        if content_rating_system:
            query.must.append(DSL_Q("nested", path="content_rating_systems", 
                query=DSL_Q("match", content_rating_systems__pk=content_rating_system)
            ))
        
        if year:
            query.must.append(DSL_Q("match", year=year))
        
        print(query)
        # print(MovieDocument.search().query(query).to_dict())

        # Por ahora hasta 100 registros (paginacion de la admin)
        s = MovieDocument.search().query(query)[:1000]
        queryset = s.to_queryset()
        # Si el order_by es solo el campo -pk... entonces se trata del orde por defecto
        # asi que pasamos de el...
        if order_by_fields and (len(order_by_fields) > 1 or not '-pk' in order_by_fields):
            queryset = queryset.order_by(*order_by_fields)
        
        if use_use_distinct:
            return queryset.distinct() if use_distinct else queryset, use_distinct
        else:
            return queryset.distinct() if use_distinct else queryset

def populate_search_filter_model(queryset, search_term, use_use_distinct=False, year=None):
    # TODO: por ahora solo para un termino... pero en un futuro deberiamos hacerlo
    # para varios
    contains_quote = False

    query_title = None
    use_distinct = False

    if search_term:
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

        

        if TitleAka.objects.filter(query_title).all().count() > 0:
            query_title = Q(title_akas__in=TitleAka.objects.filter(query_title))
            if not contains_quote:
                query_title.add(Q(title__icontains=search_term), Q.OR)
            else:
                query_title.add(Q(title__iexact=search_term), Q.OR)
            # query_title.add(Q(title_akas__in=TitleAka.objects.filter(query_title)), Q.OR)
            use_distinct = True

    if year:
        query_title_new = Q(year=year)
        
        if query_title:
            query_title_new.add(query_title, Q.AND)
        
        query_title = query_title_new

    # FIXME: investigar... Puede ocurrir que no tenga title del todo?
    # creo que no... pero por si aca :P
    if not query_title:
        return queryset, use_distinct if use_use_distinct else queryset

    # TODO: Se pueden hacer mas cosas para mejorar la busqueda... 
    # buscar tags y generos... por ahora lo vamos a dejar asi
    if use_use_distinct:
        return queryset.filter(query_title).distinct() if use_distinct else queryset.filter(query_title), use_distinct
    else:
        return queryset.filter(query_title).distinct() if use_distinct else queryset.filter(query_title)


def extract_year(search_term):
    """
    Estrae el año de los terminos de busqueda si se especifica entre parentesis
    y es un valor de 4 caracteres
    """
    if search_term.find('(') > -1 and search_term.find(')') > 3:
        year_str = re.compile('.*\(|\)').sub('', search_term)
        if year_str.isdigit():
            year = int(year_str)
            
            max_year = list(Movie.objects.aggregate(Max('year')).values())[0]
            min_year = list(Movie.objects.aggregate(Min('year')).values())[0]
            
            if year >= min_year and year <= max_year:
                search_term = re.compile(' \(.*').sub('', search_term).strip()
                return year, search_term
    
    return None, search_term

def populate_search_filter(queryset, search_term, use_use_distinct=False, genre=None, content_rating_system=None, tag=None):
    year, search_term = extract_year(search_term)

    if ELASTICSEARCH_DSL:
        return populate_search_filter_dsl(queryset, search_term, use_use_distinct=use_use_distinct, genre=genre, content_rating_system=content_rating_system, tag=tag, year=year)

    return populate_search_filter_model(queryset, search_term, use_use_distinct, year=year)

def movie_search_filter(search_term):
    return populate_search_filter(Movie.objects, search_term)