## Preparar el entorno python
* Instalar pyenv y virtualenv
```bash
# Instalamos una version de python 3.X.X
~ pyenv install 3.8.0
# Creamos un entorno para homodaba
~ pyenv virtualenv 3.8.0 homodaba
# Configuramos el directorio actual para que use el entorno creado
~ echo "homodaba" > .python-version
# Inicializamos el entorno
~ pyenv init --path
```
* Instalar dependencias
```bash
~ pip install -r python-requirements.txt
```

## Rutina (TODO: bpk)
* Generas csv con basheline
* Importas csv
   - Verificas resultados
* Compruebas con csv_2_imdb
   - Verificas resultados
   - Si hay nuevos imdb_id, volver a importar

## Pasar de sqlite3 a mysql
[source shubhamdipt.com](https://www.shubhamdipt.com/blog/django-transfer-data-from-sqlite-to-another-database/)
1. En sqlite ejecutar:
   ```bash
   manage.sh dumpdata > db.json
   ```
1. Crear la base de datos de la siguiente forma:
   ```sql
   CREATE DATABASE [DATABASE_NAME] CHARACTER SET utf8;
   ```
   Opcionalmente puedes usar  ```COLLATE utf8_bin``` que haria que la base de datos sea case sensitive (para claves, por ejemplo), si bien esto te puede ayudar para importar datos que te den error en la carga con ```manage.sh loaddata db.json```, hace que todos los filtros case-insensitive (Como __icontains, __iexact ...) sean totalmente ineficaces.
1. Cambiar la configuracion para mysql añadiendo las variables de entorno pertinentes:
   ```
   DATABASE_ENGINE='mysql'
   DATABASE_NAME='[DATABASE_NAME]'
   DATABASE_USER='[DATABASE_USER]'
   DATABASE_PASSWORD='[DATABASE_PASSWORD]'
   DATABASE_HOST='[HOST_NAME]'
   ```
1. Crear el esquema de base de datos con:
   ```bash
   manage.sh migrate
   ```
1. Borrar ContentType:
   * Nos metemos en la shell
      ```bash
      manage.sh shell
      ```
   * Borramos ContentType y todos los registros dependientes:
      ```python
      from django.contrib.contenttypes.models import ContentType
      ContentType.objects.all().delete()
      ```
1. Importar los datos ejecutando:
   ```bash
   manage.sh loaddata db.json
   ```
   - Si da algún problema del tipo :
   ```
   : Could not load data.TitleAka(pk=XXXX): (1062, "Duplicate entry 'Un titulo cualquiera' for key 'title'")

   ```
   Podemos ejecutar loaddata con la opcion "-e data.TitleAka" (para excluir de la importacion):
   ```bash
   manage.sh loaddata db.json -e data.TitleAka
   ```
   Lo unico que si hacemos esto, tendremos que corregir los titulos con:
   ```bash
   manage.sh optimize_db
   ```


## Base de datos separada para la cache
Si bien no es necesario, es recomendable tener la base de datos de cache separada de la base de datos por defecto, de esta forma podemos ignorar completamente de hacer backcup. Para empezar a usar esta base de datos extra tenemos que:
1. Establecer la variable de entorno CACHE_DATABASE=1
   - Por defecto, usara una base de datos en el mismo sitio donde esta la base de datos por defecto ("db.sqlite3") pero con el nombre "db-cache.sqlite3"
   - Si queremos usar mysql, tendremos que definir las variables entorno con la configuracion de acceso a esta base de datos:
   ```
   CACHE_DATABASE_ENGINE='mysql'
   CACHE_DATABASE_NAME='[DATABASE_NAME]'
   CACHE_DATABASE_USER='[DATABASE_USER]'
   CACHE_DATABASE_PASSWORD='[DATABASE_PASSWORD]'
   CACHE_DATABASE_HOST='[HOST_NAME]'
   ```
1. Crear la estructura de tablas:
   ```bash
   manage.sh migrate --database=cache
   ```
1. (Opcionalmente) Podemos migrar la actual cache a la nueva:
   ```bash
   manage.sh dumpdata > original-db.json
   manage.sh shell
   ```
   ```python
   from django.contrib.contenttypes.models import ContentType
   ContentType.objects.all().delete()
   ```
   ```bash
   manage.sh loaddata --database=cache original-db.json
   ```
1. (Opcionalmente) Borraremos la cache de la base de datos original:
   ```bash
   bash manage.sh delete_cache --default-database
   ```
1. (Opcionalmente) Borraremos el resto de datos que no se usan de la base de datos de cache:
   ```bash
   bash manage.sh delete_all_movies --cache-database
   ```
1. (Opcionalmente) Deberiamos borrar los datos de usuarios de la bbdd de cache (no son necesarios), pero me da perecer mirar que tablas/modelos son los que deberiamos borrar... :P

## Elastic Search
### Errores
* "Cannot operate on a closed database." al reconstruir los indices (rebuild-es.sh):
   ```
   Traceback (most recent call last):
   File "site-packages/django/db/models/sql/compiler.py", line 1602, in cursor_iter
      cursor.close()
   sqlite3.ProgrammingError: Cannot operate on a closed database.
   ```
   Mi primera impresion es que la bbdd se habia quedado pillada de alguna forma, pero no fue asi, el problema es que Elastic Search Requiere que tengas 50Gb libres de almacenamiento en el disco donde 
   lo pongas, si no tienes ese espacio, se arranca el contenedor en modo lectura.

   Lo vi al ejecutar lo siguiente: 
   ```bash
   manage.sh search_index --create
   ```

   Me dio un error distinto que googleando un poco encontre la raiz del problema:
   ```
      raise HTTP_EXCEPTIONS.get(status_code, TransportError)(
   elasticsearch.exceptions.TransportError: TransportError(429, 'cluster_block_exception', 'index [movies] blocked by: [TOO_MANY_REQUESTS/12/disk usage exceeded flood-stage watermark, index has read-only-allow-delete block];')
   ```

   Solucion: Libera espacio del disco donde tienes el ES, borra el contenedor y vuelve a crearlo.
