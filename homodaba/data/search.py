from django.db.models import Q, Max, Min

import re
from datetime import datetime

from .models import Movie, TitleAka, MoviePerson

from homodaba.settings import ELASTICSEARCH_DSL, ADMIN_MOVIE_LIST_PER_PAGE

if ELASTICSEARCH_DSL:
    from .documents import MovieDocument
    from elasticsearch_dsl import Q as DSL_Q

    def populate_search_filter_dsl(queryset, search_term, use_use_distinct=False, 
        genre=None, content_rating_system=None, tag=None, year=None, 
        director=None, writer=None, actor=None, user_tag=None):

        order_by_fields = queryset.query.order_by if queryset and queryset.query and queryset.query.order_by else None
        # TODO: stats de la busqueda (total encontrados para la paginacion)
        # TODO: paginacion
        # TODO: Analizadores de terminos para permitir busquedas por texto parcial

        query = DSL_Q('bool')

        # puede ser que busquemos solo por año, (XXXX) en ese caso no tendremos
        # mas terminos de busqueda
        if search_term:
            # Esto es un poco nyapa pero funcional:
            # Matchea terminos parciales
            query.should.append(DSL_Q("query_string", 
                query='*%s*' % search_term, 
                fields=[
                    "title^4", "title_original^4", "title_preferred^4", 
                    "directors.name^3", 
                    "writers.name^2", "casting.name^2"
                ]
            ))

            # Los objects se pueden consultar directamente sobre la consulta 
            # principal, como directores, escritores actores...
            query.should.append(DSL_Q("multi_match", 
                query=search_term, 
                fields=[
                    "title^4", "title_original^4", "title_preferred^4", 
                    "directors.name^3", 
                    "writers.name^2", "casting.name^2"
                ]
            ))

            # query='.*%s.*' % search_term

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

        if director:
            query.must.append(DSL_Q("nested", path="directors", 
                query=DSL_Q("match", directors__pk=director)
            ))
            # TODO: investigar. Esto son intentos de hacer el filtro por director
            # que no ha funcionado ni uno... revisar documents.py
            # Al final use el filtro como tag que parece que funciona :P
            # 
            # query.must.append(DSL_Q("match", directors__pk=director))
            # query.must.append(DSL_Q("multi_match", 
            #    query=director, fields=["director.pk"]
            # ))

        if writer:
            query.must.append(DSL_Q("nested", path="writers", 
                query=DSL_Q("match", writers__pk=writer)
            ))

        if actor:
            query.must.append(DSL_Q("nested", path="actors", 
                query=DSL_Q("match", actors__pk=actor)
            ))

        if genre:
            query.must.append(DSL_Q("nested", path="genres", 
                query=DSL_Q("match", genres__pk=genre)
            ))
        
        if content_rating_system:
            query.must.append(DSL_Q("nested", path="content_rating_systems", 
                query=DSL_Q("match", content_rating_systems__pk=content_rating_system)
            ))
        
        if user_tag:
            query.must.append(DSL_Q("nested", path="user_tags", 
                query=DSL_Q("match", user_tags__pk=tag)
            ))

        if year:
            query.must.append(DSL_Q("match", year=year))
        
        print(query)
        # print(MovieDocument.search().query(query).to_dict())

        # Por ahora hasta ADMIN_MOVIE_LIST_PER_PAGE registros (paginacion de la admin)
        s = MovieDocument.search().query(query)[:ADMIN_MOVIE_LIST_PER_PAGE]
        queryset = s.to_queryset()
        # Si el order_by es solo el campo -pk... entonces se trata del orde por defecto
        # asi que pasamos de el...
        if order_by_fields and (len(order_by_fields) > 1 or not '-pk' in order_by_fields):
            queryset = queryset.order_by(*order_by_fields)
        
        return queryset.distinct() if use_use_distinct else queryset, use_use_distinct

def populate_search_filter_model(queryset, search_term, use_use_distinct=False, 
    year=None, director=None, writer=None, actor=None, 
    genre=None, content_rating_system=None, tag=None, user_tag=None):

    # TODO: por ahora solo para un termino... pero en un futuro deberiamos hacerlo
    # para varios
    contains_quote = False

    search_query = None

    if search_term:
        if search_term.startswith('"'):
            contains_quote = True
            search_term = search_term[1:]
        if search_term.endswith('"'):
            contains_quote = True
            search_term = search_term[:-1]

        if not contains_quote:
            search_query = Q(title__icontains=search_term)
            search_query.add(Q(title_original__icontains=search_term), Q.OR)
            search_query.add(Q(title_preferred__icontains=search_term), Q.OR)
        else:
            search_query = Q(title__iexact=search_term)
            search_query.add(Q(title__icontains=' ' + search_term), Q.OR)
            search_query.add(Q(title__icontains=search_term + ' '), Q.OR)
            search_query.add(Q(title_original__iexact=search_term), Q.OR)
            search_query.add(Q(title_original__icontains=' ' + search_term), Q.OR)
            search_query.add(Q(title_original__icontains=search_term+ ' '), Q.OR)
            search_query.add(Q(title_preferred__iexact=search_term), Q.OR)
            search_query.add(Q(title_preferred__icontains=' ' + search_term), Q.OR)
            search_query.add(Q(title_preferred__icontains=search_term+ ' '), Q.OR)

    if year:
        search_query_new = Q(year=year)
        
        if search_query:
            search_query_new.add(search_query, Q.AND)
        
        search_query = search_query_new

    if director:
        search_query_new = Q(directors__pk=director)

        if search_query:
            search_query_new.add(search_query, Q.AND)
        
        search_query = search_query_new

    if writer:
        search_query_new = Q(writers__pk=writer)

        if search_query:
            search_query_new.add(search_query, Q.AND)
        
        search_query = search_query_new

    if actor:
        search_query_new = Q(actors__pk=actor)

        if search_query:
            search_query_new.add(search_query, Q.AND)
        
        search_query = search_query_new

    if genre:
        search_query_new = Q(genres__pk=genre)
        
        if search_query:
            search_query_new.add(search_query, Q.AND)
        
        search_query = search_query_new

    if content_rating_system:
        search_query_new = Q(content_rating_systems__pk=content_rating_system)
        
        if search_query:
            search_query_new.add(search_query, Q.AND)
        
        search_query = search_query_new

    if tag:
        search_query_new = Q(tags__pk=tag)
        
        if search_query:
            search_query_new.add(search_query, Q.AND)
        
        search_query = search_query_new

    if user_tag:
        search_query_new = Q(user_tags__pk=user_tag)
        
        if search_query:
            search_query_new.add(search_query, Q.AND)
        
        search_query = search_query_new

    if search_query:
        queryset = queryset.filter(search_query)

    return queryset.distinct() if use_use_distinct else queryset, use_use_distinct


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
                search_term = re.compile('\(.*').sub('', search_term).strip()
                return year, search_term
    
    return None, search_term

def populate_search_filter(queryset, search_term, use_use_distinct=False, 
    genre=None, content_rating_system=None, tag=None, 
    director=None, writer=None, actor=None, 
    user_tag=None):
    year, search_term = extract_year(search_term)

    if ELASTICSEARCH_DSL:
        return populate_search_filter_dsl(queryset, search_term, 
            use_use_distinct=use_use_distinct, genre=genre, 
            content_rating_system=content_rating_system, tag=tag, 
            year=year, director=director, writer=writer, actor=actor, user_tag=user_tag
        )

    return populate_search_filter_model(queryset, search_term, use_use_distinct, 
        year=year, director=director, writer=writer, actor=actor, genre=genre, 
        content_rating_system=content_rating_system, tag=tag, 
        user_tag=user_tag
    )

def movie_search_filter(search_term):
    return populate_search_filter(Movie.objects, search_term)