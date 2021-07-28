2021-03-28:
  * Añadiendo comando para borrar cache
  * Separando todo en archivo independiente todo.md
  * Variable ADMIN_MOVIE_LIST_PER_PAGE para definir el tamaño de paginado con las busquedas de pelis (por defecto 100)
  * Añadiendo soporte para mysql

2021-03-08:
  * Añadido soporte a fichero JSON con los campos que se quieren cambiar. El formato debe ser similar a:
    ```
    [
    {"search": {"title": "The Phantom Menace"}, "replace": {"title": "Star Wars: Episode I - The Phantom Menace"}},
    {"search": {"title": "Superman II", "year": "2006"}, "replace": {"title": "Superman II", "version": "Richard Donner edition", "year": "1980", "tag": "2006", "director": "Richard Lester"}}
    ]
    ```

2021-02-16:
  * Django config cambiada para escuchar en la red local.
  * SECRET_KEY sacada del código. Debe estar definida como variable de
  entorno.
  * LOCALNETIP añadida como variable de entorno para definir en qué IP
  escucha el servicio además de localhost.
  * Bas(h)line ahora crea el CSV partiendo de ficheros TXT y CSV:
    - TXT File: `find /path > file.TXT`
    - CSV File headers: `Localizacion;Título Original;Titulo traducido;Director;Año;Resolución;Formato`


2020-09-10:
  * reemplazando verbose por el argumento verbosity para import_csv
  * añadiendo clasificaciones por edad a Movie (migrate)
  * creando ejemplo de actualizacion de datos a partir de imdb_raw_data
  * mostrando los tipos de medios disponibles en la busqueda de pelis
  * empezando con telegrambot (creando app a parte)
  * creando este changelog ^_^
