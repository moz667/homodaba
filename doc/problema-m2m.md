### El problema: Tener una relacion de directores en la tabla Movie que te permita filtrar peliculas solo por director. 

 * #### Primera aproximacion:
    - En teoria, al tratarse de una tabla intermedia personalizada (MoviePerson, tiene el campo role que define como se comporta la persona en la pelicula) se deberia hacer con un Proxy y un manager, tal y como lo hacemos aqui:

        ```python
        class Movie(models.Model):
            ...
            # Esto tiene miga... para mantener la relacion m2m a Person a traves de 
            # MoviePerson, por ser un modelo a medida, se tiene que hacer a traves
            # del proxy: MoviePersonDirectorProxy
            directors = models.ManyToManyField(Person, through='MoviePersonDirectorProxy', blank=True)
            # people = models.ManyToManyField('MoviePerson', related_name='people')
            # people = MoviePersonDirectorManager()

        # Manager y Proxy para las relaciones que se pudieran sacar
        # de directores solo (role=MoviePerson.RT_DIRECTOR), esto se hace
        # para simplificar este tipo de relaciones (ahora mismo se esta usando
        # para sacar directors en Movie)
        class MoviePersonDirectorManager(models.Manager):
            def get_queryset(self):
                print("get_queryset")
                return super().get_queryset().filter(role=MoviePerson.RT_DIRECTOR)
            
            def get_prefetch_queryset(self, instances, queryset=None):
                print("get_prefetch_queryset")
                return super().get_prefetch_queryset(instances, queryset).filter(role=MoviePerson.RT_DIRECTOR)

        class MoviePersonDirectorProxy(MoviePerson):
            objects = MoviePersonDirectorManager()
            
            # Esto no deberia ser necesario, pero vi que los Model tenian estos metodos
            # XXX_queryset y decidi ponerlos por probar
            def get_queryset(self):
                print("MoviePersonDirectorProxy.get_queryset")
                return super().get_queryset().filter(role=MoviePerson.RT_DIRECTOR)

            def get_prefetch_queryset(self, instances, queryset=None):
                print("MoviePersonDirectorProxy.get_prefetch_queryset")
                return super().get_prefetch_queryset(instances, queryset).filter(role=MoviePerson.RT_DIRECTOR)

            def __init__(self):
                print("MoviePersonDirectorProxy.__init__")
                super().__init__(self)

            class Meta:
                print("MoviePersonDirectorProxy.Meta")
                proxy = True
        # ^^^^^^^^^^^^
        ```
    - Resultado, se lo traga bien y en apariencia funciona, pero lo que realmente esta haciendo es la relacion de personas que trabajan en la pelicula pasando del filtro de role.
    
        Para comprobar este comportamiento podemos hacer la siguiente prueba:

        ```python
        >>> from data.models import Movie, MoviePerson, Person
        >>> ss = Person.objects.filter(name__icontains='Steven Spielberg').all()[0]
        >>> ss
        <Person: Steven Spielberg>
        >>> for m in Movie.objects.filter(directors__pk=ss.id).all():
        ...     for d in m.directors.all():
        ...             print(d.name)
        ```

        Si nos fijamos bien, te saca todas las pelis en las que "Steven Spielberg" 
        ha participado, inclusive en las que que no es director. Por esto esta solucion
        no nos vale.

        Puse las trazas (ver print anteriores) para ver cuando se metia en xxx_queryset
        con los filtros, y el tema es que no se mete NUNCA!!!

        Con lo que cada vez que filtraramos por director, teniamos que ñapear haciendo 
        una seleccion de directores para la peli en cuestion, como en  este caso: 
        (sacado de MovieAdmin.get_search_results):

        ```python
        director_filter = None

        if 'directors__pk__exact' in request.GET.keys():
            if request.GET['directors__pk__exact']:
                director_filter = int(request.GET['directors__pk__exact'])
                movie_ids = []
                for mp in MoviePerson.objects.filter(person__pk=director_filter, role=MoviePerson.RT_DIRECTOR).all():
                    movie_ids.append(mp.movie.id)
                
                queryset = queryset.filter(id__in=movie_ids)
                # print(queryset.query)
                # print(dir(queryset))
                # print(movie_ids)
        ```

        o esto en populate_search_filter_model:
        
        ```python
        if director:
            movie_ids = []
            for mp in MoviePerson.objects.filter(person__pk=director, role=MoviePerson.RT_DIRECTOR).all():
                movie_ids.append(mp.movie.id)
            
            search_query_new = Q(id__in=movie_ids)

            if search_query:
                search_query_new.add(search_query, Q.AND)
            
            search_query = search_query_new
        ```

 * #### Segunda aproximacion: 
    - Mostrar la relacion con MoviePerson tal cual, es decir algo asi:

        ```python
        class Movie(models.Model):
            ...
            movie_persons = models.ManyToManyField('MoviePerson', through='MoviePersonProxy', blank=True)

        class MoviePersonProxy(MoviePerson):
            class Meta:
                proxy = True
        ```
    - Resultado:
        ```python
        ERRORS:
        data.Movie.movie_persons: (fields.E303) Reverse query name for 'Movie.movie_persons' clashes with field name 'MoviePerson.movie'.
            HINT: Rename field 'MoviePerson.movie', or add/change a related_name argument to the definition for field 'Movie.movie_persons'.
        data.MoviePersonProxy: (fields.E336) The model is used as an intermediate model by 'data.Movie.movie_persons', but it does not have a foreign key to 'Movie' or 'MoviePerson'.
        ```

 * #### Tercera aproximacion: 
    - Recorde una app que he usado y que mola bastante para poder ordenar relaciones ManyToMany, asi que mire un poco como hacia el tipo de campo ordenable para ver si de esa forma conseguia que funcionara (la app ordena, nosotros filtramos
    algo mas o menos tiene que hacer). La idea, en resumen, seria hacer un ManyToManyField personalizado:

        Mas info de la app sortedm2m [https://github.com/jazzband/django-sortedm2m/blob/master/sortedm2m/fields.py]

        ```python
        from django.db import models, router, transaction
        from django.db.models import Max, Model, signals
        from django.db.models.fields.related import ManyToManyField as _ManyToManyField
        from django.db.models.fields.related import lazy_related_operation, resolve_relation
        from django.db.models.fields.related_descriptors import ManyToManyDescriptor, create_forward_many_to_many_manager
        from django.db.models.utils import make_model_tuple
        from django.utils.encoding import force_str
        from django.utils.functional import cached_property
        from django.utils.translation import gettext_lazy as _

        def create_sorted_many_related_manager(superclass, rel, *args, **kwargs):
            RelatedManager = create_forward_many_to_many_manager(
                superclass, rel, *args, **kwargs)

            class SortedRelatedManager(RelatedManager):
                def get_queryset(self):
                    print("SortedRelatedManager.get_queryset")
                    return super().get_queryset().filter(role='director')

                def get_prefetch_queryset(self, instances, queryset=None):
                    print("SortedRelatedManager.get_prefetch_queryset")
                    return super().get_prefetch_queryset(instances, queryset).filter(role='director')

            return SortedRelatedManager


        class SortedManyToManyDescriptor(ManyToManyDescriptor):
            def __init__(self, field):
                super().__init__(field.remote_field)

            @cached_property
            def related_manager_cls(self):
                model = self.rel.model
                return create_sorted_many_related_manager(
                    model._default_manager.__class__,  # pylint: disable=protected-access
                    self.rel,
                    # This is the new `reverse` argument (which ironically should
                    # be False)
                    reverse=False,
                )

        class SortedManyToManyField(_ManyToManyField):
            # Providing a many to many relation that remembers the order of related
            # objects.
            # 
            # Accept a boolean ``sorted`` attribute which specifies if relation is
            # ordered or not. Default is set to ``True``. If ``sorted`` is set to
            # ``False`` the field will behave exactly like django's ``ManyToManyField``.
            # 
            # Accept a class ``base_class`` attribute which specifies the base class of
            # the intermediate model. It allows to customize the intermediate model.

            def __init__(self, to, **kwargs):  # pylint: disable=redefined-builtin
                super().__init__(to, **kwargs)

            def get_internal_type(self):
                return 'ManyToManyField'

            # pylint: disable=inconsistent-return-statements
            def contribute_to_class(self, cls, name, **kwargs):
                # Add the descriptor for the m2m relation
                # moz667: Aqui es donde puede estar el fallo... 
                # lo mismo hay que hacerlo en orden inverso, primero contribute_to_class
                # y despues el setattr... pero me canse de probar
                setattr(cls, name, SortedManyToManyDescriptor(self))
                return super().contribute_to_class(cls, name, **kwargs)

        def create_sortable_many_to_many_intermediary_model(field, klass, sort_field_name, base_classes=None):
            def set_managed(model, related, through):
                through._meta.managed = model._meta.managed or related._meta.managed

            to_model = resolve_relation(klass, field.remote_field.model)
            name = '%s_%s' % (klass._meta.object_name, field.name)
            lazy_related_operation(set_managed, klass, to_model, name)
            base_classes = base_classes if base_classes else (models.Model,)

            # TODO : use autoincrement here ?
            sort_field = models.IntegerField(default=0)

            to = make_model_tuple(to_model)[1]
            from_ = klass._meta.model_name
            if to == from_:
                to = 'to_%s' % to
                from_ = 'from_%s' % from_

            meta = type('Meta', (), {
                'db_table': field._get_m2m_db_table(klass._meta),  # pylint: disable=protected-access
                'auto_created': klass,
                'app_label': klass._meta.app_label,
                'db_tablespace': klass._meta.db_tablespace,
                'unique_together': (from_, to),
                'ordering': (sort_field_name,),
                'verbose_name': _('%(from)s-%(to)s relationship') % {'from': from_, 'to': to},
                'verbose_name_plural': _('%(from)s-%(to)s relationships') % {'from': from_, 'to': to},
                'apps': field.model._meta.apps,
            })

            # Construct and return the new class.
            return type(force_str(name), base_classes, {
                'Meta': meta,
                '__module__': klass.__module__,
                from_: models.ForeignKey(
                    klass,
                    related_name='%s+' % name,
                    db_tablespace=field.db_tablespace,
                    db_constraint=field.remote_field.db_constraint,
                    on_delete=models.CASCADE,
                ),
                to: models.ForeignKey(
                    to_model,
                    related_name='%s+' % name,
                    db_tablespace=field.db_tablespace,
                    db_constraint=field.remote_field.db_constraint,
                    on_delete=models.CASCADE,
                ),
                # Sort fields
                sort_field_name: sort_field,
                '_sort_field_name': sort_field_name,
            })
        ```
    - Resultado, pasa lo mismo que en la primera aproximación, no pasa por los xxx_queryset
