
## Update de cinemagoer a 2025.5.19 (git)

**In progress**

Con la ultima importacion he visto que no se estaba añadiendo portadas ni directores ni actores, revisando distintas opciones, vi que [imdbapi.dev](https://imdbapi.dev/) podría ser una mejora considerable, pero requiere que cambiemos bastante codigo.

Revisando tambien la actual libreria que estamos usando de [cinemagoer](https://github.com/cinemagoer/cinemagoer), tiene actualizaciones pero no esta generando relases y te recomienda que uses el repo directamente.

Despues de hacer unas pruebas, parece que va algo mejor aunque aun faltan cosas por arreglar:


## Tareas usando nuevas APIs

* [X] Probar tmdb api (themoviedatabase.org), aunque hay clientes de api parecen bastante antiguos
  * [X] ~~El problema de tmdb es que no tiene imdbid~~ Si tiene, se puede buscar por el inclusive
  * [ ] ~~titulo original en caracteres latinos~~ No lo acabo de ver claro... quias en otra ocasion
  * [X] titulo internacional
  * [X] titulo en castellano
  * [X] posibilidad de buscar por titulo y año para acotar
  * [X] poster
  * [X] directores
  * [X] escritores
  * [X] actores
  * [X] Que en la busqueda tengamos
    * [ ] ~~Directores~~ No tiene
    * [ ] ~~imdb_id~~ No tiene
    * [ ] ~~titulo original~~ No tiene
    * [X] titulo internacional
    * Con el id conseguimos el resto de datos (en el detalle de la peli)
  * [X] Que en el detalle tengamos
    * [X] ~~Coger peli por imdb_id~~ No lo tiene pero se puede conseguir el id de tmdb buscando por imdb_id (con `Find`)

* [X] Nueva funcionalidad
  * [X] Permitir importar pelis que no encuentra

* [ ] Cambios en el modelo
  * [X] ImdbCache
    * [X] Cambiar de nombre por algo mas generico (APICache)
    * [X] Modificar la estructura a algo tipo clave/valor
    * [X] Tener una estrategia para generar la clave independientemente del:
      * tipo de API
      * Si es una busqueda, detalle, etc...
  * [X] Person
    * [X] Añadir campo tmdb_id (Modificar la creacion de Person para que pille el nuevo campo)
  * [ ] TitleAka
    * [ ] Añadir un campo con un subtipo de pais (algo generico en plan zone)
  * [ ] ~~Country~~
    * [ ] ~~Añadir un campo con el codigo iso_3166_1 y que sea unico~~
  * [X] Movie
    * [X] Añadir campo tmdb_id (Modificar la creacion de Movie para que pille el nuevo campo)

* [ ] Pruebas
  * [X] Nuevo comando de busqueda
  * [X] Probar el resto de la aplicacion (que ponemos aqui?)
    * [X] Probar escaneo de directorios
    * [X] Probar importar csv (con imdb_id)
    * [X] Probar importar csv (sin imdb_id)
  * [X] OJO: la nueva api abusa de microservicios (el detalle de una pelicula es minimo y va cargando info, haciendo mas peticiones al resto de datos, segun accedemos a metodos, como por ejemplo `info` o `credits`), comprobar que almacena la api_key y ver que podemos hacer... quizas almacenar la FacadeMovie y olvidarnos de almacenar la Movie devuelta con la API?
  * [ ] Probar telegram bot
  * [X] Probar elasticache **No funciona!**

* [ ] Problemas:
  * [ ] Problema con `title_akas` (la clave por pais se repite: euskera, catala los pone como ES pero con distinto type)
  * [X] El pais de origen de la peli ahora se guarda como iso y se muestra como tal. Convertir a nombre de pais.
  * [X] No funciona el filtro por persona
  * [X] Tamaño de las miniaturas en la admin (es tochillo)
  * [X] Tamaño de las miniaturas en la busqueda (es tochillo)

* [X] Casos extremos (para luego):
  * [X] It 1990 (tv mini-serie) **Pass**
    * [X] Se encuentra por imdb_id (`https://api.themoviedb.org/3/movie/1618880?api_key=<API_KEY>`) pero no tiene casi informacion ¿que hacemos?
      * Buscando por tv (es una mini serie de 2 episodios) la encuentra y tiene first_air_date que podria valer en vez de release_date...
      * `https://api.themoviedb.org/3/search/tv?query=It&include_adult=false&language=en-US&page=1&year=1990&api_key=<API_KEY>`
      * Pero no tiene director en los creditos
      * `https://api.themoviedb.org/3/tv/19614/credits?language=en-US&api_key=<API_KEY>`
      * Asi que los problemas que veo son que al usar los datos de tv son:
        * Las estructuras de datos respecto a movie son muy distintos
        * No comparten id (son diferentes el id de tv que el de movie)
        * No veo datos completos (no hay director, ni escritor)
      * Conclusion: Vamos a pasar de TV por ahora
    * [X] El faro, 1998 (`NO_CACHE=1 python3 ./manage.py search_movie --title "El faro" --year 1998`)
      * Apaña buscando por imdb_id: `NO_CACHE=1 python3 ./manage.py search_movie --imdb_id tt0168749`
    * [X] Ifigenia, 1968 (`NO_CACHE=1 python3 ./manage.py search_movie --title "Ifigenia" --year 1968`)
      * No se encuentra por imdb_id: `NO_CACHE=1 python3 ./manage.py search_movie --imdb_id tt6696960` 
      * Va a pasar lo mismo que con It, al ser de TV (visto en [imdb](https://www.imdb.com/title/tt6696960/)) pasamos por ahora 

## Elasticsearch

Elasticsearch ha dejado de funcionar con las ultimas versiones de homodaba, como tampoco se estaba usando lo vamos a dejar como una tarea pendiente de revisar.

Para poder probar elastic search hay que hacer lo siguiente al compose:

1. Añadir el argumento de construccion `ELASTICSEARCH: true` a la imagen de la app principal
2. Añadir al entorno la variable que especifica a la app la localizacion del servicio de elasticsearch, `- ES_DSL_HOSTS=http://dev-elasticsearch:9200`
3. Añadir el servicio con el elasticsearch (ver mas abajo con caracteristicas del mismo en el servicio `dev-elasticsearch`)

**Ejemplo de compose:**
```yaml
services:
    ...
    dev-app:
        extends:
            service: app
            file: docker-compose.base.yml
        build:
            args:
                ...
                ELASTICSEARCH: true
        ...
    dev-elasticsearch:
        image: docker.elastic.co/elasticsearch/elasticsearch:9.2.5
        restart: always
        environment:
            - discovery.type=single-node
            - xpack.security.enabled=false
        ulimits:
            memlock:
                soft: -1
                hard: -1
        volumes:
            - esdata:/usr/share/elasticsearch/data

volumes:
  esdata:
    driver: local

```

### Tareas pendientes de elasticsearch

* [ ] No funciona la creacion/rellenado de indices Error: `elastic_transport.ConnectionTimeout: Connection timed out` al ejecutar:
  * `python manage.py search_index --create` (crea el indice pero no lo rellena con valores)
  * `python manage.py search_index --populate`
* [ ] No funciona la busqueda (seguramente porque no tenemos indices), por ejemplo accediendo a: `http://127.0.0.1:8000/homodaba/movies/?director=&writer=&actor=&tag=&genre=&cr_system=&user_tag=&unseen=&order_by=&search_term=Zach`


## Pendientes
1. [ ] Usar [pyproject-toml](https://pip.pypa.io/en/stable/reference/build-system/pyproject-toml/)
1. [ ] Favicon
1. [ ] Cambiar la nomenclatura de las variables de entorno que se usan en la app para que empiecen todas con HDB_. Esto nos daria pistas para a simple vista ver si se trata de una variable de nuestra app o por el contrario es una variable de algun otro servicio.
1. [ ] Quitar todo el tema este de variables para compartir por http e incluirlo en la importacion como un tipo de storage_type mas

### Funcionalidades
1. [ ] Añadir descripcion a las tags... esto nos puede servir por ejemplo para poner order de visionado de sagas que tengan varias pelis
1. [ ] Aplicar tags desde la web como usuario no staff a las pelis
1. [ ] En la busqueda de peliculas, buscar el texto en terminos y sacarlo como enlaces de filtro de busqueda:
    * Tag
    * GenreTag
    * ContentRatingTag
    * UserTag
    * Person

### Limpieza de dockers
1. [ ] Reorganizar todo el tema de shell scripts (movido por ahora a [zzz-oldcode](./zzz-oldcode))
1. [X] ~~Añadir a la version dev un mysql~~
1. [ ] health check de contenedores
1. [ ] Documentar opciones de despliegue:
    * MySql
    * Telegram Bot (tbot)
    * Elastic Search (es)
    * Estaticos: watch & build

### Bugs

### General
1. [ ] Documentar en general (uff... que pereza  ^ _ ^)
    - [ ] Entorno pyenv homodaba : homodaba (created from 3.8.3)
    - [ ] Variables de entorno
1. [ ] Ver qué hacemos con las películas que no están en IMDB.

### Funcionalidad
1. [ ] Busqueda por texto en participantes (peli o nombre de persona)
1. [ ] Actualizacion de imdb_id desde la admin:
    Esto es una idea que puede estar bien, tener la posibilidad de cambiar el imdb_id a una peli que localizamos esta mal, el problema es que deberiamos tambien guardar la relacion con la peli antigua y la nueva, para que las futuras importaciones de ese archivo coincida con el nuevo imdb_id... pensar en esto
1. [ ] Transcoding / Download
1. [X] ~~Tag de usuario para marcar pelis vistas~~
1. [ ] Como comprobamos que un medio ha sido eliminado?

### Modelo
1. [ ] Añadir campo para orden de visionado (para que bpk no este metiendo una tag por cada peli dentro de una saga :P)
1. [ ] Pillar los kind de iMDBPy : https://github.com/alberanid/imdbpy/blob/master/imdb/utils.py
1. [ ] Añadir en MovieStorageType un campo que defina el tamaño del archivo
1. [X] ~~problemas con el filtro de director (filtra por cualquiera de la peli)
1. [ ] Hacer lo mismo que hemos hecho para directors en Movie para el resto de casting.. lo mismo tener un writers, actors y casting (que tenga todos)
1. [X] ~~quitar toda la morralla del minidetail y limpiar~~
1. [ ] Meter slugs en Tags, Personas y Pelis (Para no dependender del id que cambia mucho con las limpiezas que hacemos)
1. [ ] Posibilidad de alamacenar el tamaño del medio (interesante para re-ripear)

### Cache
1. [X] ~~Sacar la cache y ponerlo en una app a parte. Quizas, opcionalmente, usar una bbdd alternativa para la cache~~
1. [ ] Cachear las imagenes de las portadas?
1. [ ] Poner fecha de caducidad a la cache (ImdbCache)
1. [X] ~~quitar los raw de la base de datos (con la cache yo creo que nos basta) (esto nos obliga a quitar los sample_XXX.py de data/management/commands)~~
1. [ ] Hacer algun comando para regenerar la cache (igual aplicarlo en el optimize_db)

### Telegram Bot
1. [ ] Sacar caratula en busquedas
1. [ ] Logear accesos
1. [ ] Autenticar de alguna forma
1. [ ] Hacer algo para cuando son muchos resultados (atachear fichero? paginar?)

### Elastic Search
1. [ ] Leer como funciona elastic search y ampliar esto :P

### Homodaba
1. [ ] Parametrizar el PATH soportado por basheline (`/media/bpk/(HDD-(?:Pelis|Anime)-[0-9]{3})/([HS]D)`)

### Rendimiento


## Terminado

### Bugs
1. [X] ~~Fallo al importar datos de sqlite3... title en TitleAka duplicado!!!~~
1. [X] ~~ref="noopener noreferrer" en los enlaces fuera (imgs, o imdb)~~
1. [X] ~~Busqueda por año~~
1. [X] ~~no importa tags nueva para un medio nuevo de peli existentes a traves del import_csv~~
1. [ ] Eliminar `HOMODABA_MINI_DETAILS` del código.

### Public no staff
1. [X] ~~link a imdb en la carátula~~
1. [X] ~~quitar ultimos medios (tiene una utilidad puntual)~~
1. [X] ~~titulo original mal en algunas pelis
1. [X] ~~Paginacion en busquedas (con infinite)~~
1. [X] ~~Ordenacion de resultados~~

### Limpiando titulos
1. [X] ~~Ver qué hacemos con las películas cuyo título original no es en inglés. El IMDB usa "World-wide (English title)" en lugar de "original title".~~
1. [X] ~~Problema con los akas (si buscas love te saca pelis con el titulo en sloveno)~~
1. [X] ~~Para calcular el titulo original si tiene varios paises coger el primero de los akas que coincida con el primer pais, sino el segundo... etc... (por orden)~~
1. [X] ~~Datos incorrectos en los campos title de Movie, Ejemplos (title, title_original, title_preferred):~~
    - ~~Suicide Squad, Bravo 14, Escuadrón suicida~~
    - ~~Blue Is the Warmest Colour, Blue Is the Warmest Colour, La vida de Adèle~~

### Rendimiento
1. [X] ~~Hacer que pille menos datos, las tablas mas cargadas son:~~
    - ~~MoviePerson, Person (seguramente pillar solo directores, escritores y primeros 6 actores)~~
    - ~~TitleAka (pillar solo los titulos que entendemos pueden ser interesantes o tener inclusive la opcion de pasar de esos titulos, con los tres que guardamos en Movie deberia ser suficiente)~~
1. [X] ~~Configurar por settings el tamaño de paginacion de la busqueda de peliculas~~
1. [X] ~~Usar MySql~~

### Funcionalidad
1. [X] ~~Escaneo de directorios para buscar nuevos o seguir usando csvs?~~
1. [X] ~~Busqueda de peliculas en admin:~~
    - ~~Hacer opcional que saque otros titulos (no tiene mucho sentido)~~
    - ~~Mostrar forma alternativa de medios en las que solo saque la ruta~~
1. [X] ~~marcar para ver mas tarde (con tag que sea XXX-nombre de user)~~
1. [X] ~~Borrar tablas con truncate en vez de delete (ver delete_all_movies.py)~~
1. [X] ~~Generar tags por las decadas~~

### Diseño
1. [X] ~~Hacer responsive la lista de peliculas de la admin (o lo mismo hacer una plantilla para el tema de busqueda... la admin esta bien pero tiene muchas cosas de django que lo mismo nos la soplan)~~
    - ~~Estoy dandole vueltas a esto y creo que lo mejor al final va a ser sacar una vista especial para las busquedas (y dejar la admin como estaba al principio :P)~~
1. [X] ~~Mirar themes de admin con bootstrap~~

## Mesh
