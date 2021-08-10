## Pendientes

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
1. [ ] Tag de usuario para marcar pelis vistas
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

### Rendimiento


## Terminado

### Bugs
1. [X] ~~Fallo al importar datos de sqlite3... title en TitleAka duplicado!!!~~
1. [X] ~~ref="noopener noreferrer" en los enlaces fuera (imgs, o imdb)~~
1. [X] ~~Busqueda por año~~
1. [X] ~~no importa tags nueva para un medio nuevo de peli existentes a traves del import_csv~~

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