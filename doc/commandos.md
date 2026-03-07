# Comandos

Documentacion a modo de resumen de lo que hacen todos los comandos del `manage.py` (al menos por ahora, lo mismo algun dia podemos completarlo mas)

## app data

### check_db_inconsistencies

Utilizado para buscar problemas en la base de datos, en la actualidad solo busca si hay duplicados en los campos `title akas`, "Titulos conocidos (akas)" en la admin.

### check_mst

Comprueba si una lista de peliculas definidas en un csv tiene tipo de almacenamiento (`MovieStorageType`) y si coincide su almacenamiento con el de otra pelicula dada de alta.

El tipo de almacenamiento es un dato que permitimos que no sea único, aunque es muy poco probable que dos peliculas distintas tenga el mismo almacenamiento dos veces.

Excluye versiones no digitales, es decir, no comprueban tipo de almacenamiento que sean `not is_original`.

### clean_filenames

Escanea un directorio por todos los archivos de medios, subtitulos, audios... y 

### csv_to_imdb

Comprueba que los datos del csv se pueden encontrar en la api consultada externa

### delete_all_movies

Borra peliculas, y opcionalmente otros datos (inclusive cache)

### delete_cache

Borra la base de datos de cache (repetido en delete_all_movies)

### import_csv

Importa datos del csv en homodaba

### normalize_age_certificates

Normaliza los distintos valores de certificacion de edad (ya no se usa este campo desde que usamos tmdb api)

### optimize_db

Optimiza la base de datos y reduce el numero de relaciones de peliculas con otras entidades como TitleAka y MoviePerson

### scan_directories

Escanea en busca de medios un directorio y genera un csv para poder importar
<!-- TODO: Ya puestos podriamos poner una opcion para guardar en homodaba los que no esten -->

### search_movie

Busca peliculas (usando homodaba y la api de terceros)

## app homodaba

### start_telegram_bot

Arranca el bot para telegram, este comando solo esta disponible si construyes la imagen con el argumento `ARG TELEGRAM`.
