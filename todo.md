### Bugs
1. [ ] Fallo al importar datos de sqlite3... title en TitleAka duplicado!!!

### General
1. [ ] Documentar el pyenv homodaba : homodaba (created from 3.8.3)
1. [ ] Documentar (uff... que pereza  ^ _ ^)
1. [ ] Ver qué hacemos con las películas que no están en IMDB.

### Funcionalidad
1. [ ] Escaneo de directorios para buscar nuevos o seguir usando csvs?
1. [ ] Busqueda por texto en participantes (peli o nombre de persona)
1. [ ] Busqueda de peliculas en admin:
    - Hacer opcional que saque otros titulos (no tiene mucho sentido)
    - Mostrar forma alternativa de medios en las que solo saque la ruta
1. [ ] Actualizacion de imdb_id desde la admin:
    Esto es una idea que puede estar bien, tener la posibilidad de cambiar el imdb_id a una peli que localizamos esta mal, el problema es que deberiamos tambien guardar la relacion con la peli antigua y la nueva, para que las futuras importaciones de ese archivo coincida con el nuevo imdb_id... pensar en esto

### Diseño
1. [ ] Hacer responsive la lista de peliculas de la admin (o lo mismo hacer una plantilla para el tema de busqueda... la admin esta bien pero tiene muchas cosas de django que lo mismo nos la soplan)

### Modelo
1. [ ] Añadir campo para orden de visionado (para que bpk no este metiendo una 
tag por cada peli dentro de una saga :P)
1. [ ] Pillar los kind de iMDBPy : https://github.com/alberanid/imdbpy/blob/master/imdb/utils.py
1. [ ] Añadir en MovieStorageType un campo que defina el tamaño del archivo
1. [ ] Poner fecha de caducidad a la cache (ImdbCache)

### Limpiando titulos
1. [ ] Ver qué hacemos con las películas cuyo título original no es en inglés. El IMDB usa "World-wide (English title)" en lugar de "original title".
1. [ ] Problema con los akas (si buscas love te saca pelis con el titulo en sloveno)
1. [ ] Para calcular el titulo original si tiene varios paises coger el primero de los akas que coincida con el primer pais, sino el segundo... etc... (por orden)
1. [ ] Datos incorrectos en los campos title de Movie, Ejemplos (title, title_original, title_preferred):
    - Suicide Squad, Bravo 14, Escuadrón suicida
    - Blue Is the Warmest Colour, Blue Is the Warmest Colour, La vida de Adèle

### Rendimiento
1. [ ] Hacer que pille menos datos, las tablas mas cargadas son:
    - MoviePerson, Person (seguramente pillar solo directores, escritores y primeros 6 actores)
    - TitleAka (pillar solo los titulos que entendemos pueden ser interesantes o tener inclusive la opcion de pasar de esos titulos, con los tres que guardamos en Movie deberia ser suficiente)
1. [ ] Configurar por settings el tamaño de paginacion de la busqueda de peliculas
1. [X] ~~Usar MySql~~

### Telegram Bot
1. [ ] Sacar caratula en busquedas
1. [ ] Logear accesos
1. [ ] Autenticar de alguna forma
1. [ ] Hacer algo para cuando son muchos resultados (atachear fichero? paginar?
