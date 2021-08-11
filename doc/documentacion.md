# Instalación de HoMoDaba en Linux
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

## Obtenemos una nueva SECRET_KEY
Todas las instalaciones de Django sequieren una SECRET_KEY única (ref. [Documentación de Django#secret-key](https://docs.djangoproject.com/en/dev/ref/settings/#secret-key))
1. Creamos una nueva secret-key:
```bash
~ python homodaba/manage.py shell -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```
2. Exportamos el valor devuelto por el comando anterior al fichero de configuración.
```bash
~ echo "export SECRET_KEY='XX_RANDOM_AND_WEIRD_STRING_XX'" >> .venv
```


## [OPCIONAL] Definimos otros parámetros de configuración en .venv
Todos los parámetros, con la excepción del parámetro SECRET_KEY previamente definido, son opcionales:
```bash
# Desactivamos el modo debug de Django. Recomendado si se va a exponer el servicio en Internet.
export DJANGO_DEBUG=False

# IP y FQDN donde Django sirve el contenido.
# Ejemplo publicando Django a través de IP y el dominio dominio.net
# Más información en: https://docs.djangoproject.com/en/3.1/ref/settings/#allowed-hosts
export ALLOWED_HOSTS="127.0.0.1 localhost 10.100.12.10 dominio.net"

# PATH donde se publicará la aplicación. Si no se especifica, la aplicación se publicará en el path raíz, por ejemplo http://dominio.net/
export HOME_URL_PATH="homodaba/"

# Usar una base de datos dedicada para caché.
export CACHE_DATABASE=1

# Especificamos el número de elementos por página que devuelve la interfaz admin de Django.
export ADMIN_MOVIE_LIST_PER_PAGE=100
```

# Instalación de versión dockerizada de HoMoDaBa (con docker-compose)
<details>
  <summary>TODO</summary>
  Cómo desplegar HoMoDaBa con docker-compose
</details>

# Tareas recurrentes
## Arrancar la aplicación
Para arrancar la aplicación:
```bash
~ ./start.sh
```

Conectarse a la aplicación a través de http://dominio.net:8000/homodaba/

Por defecto Django escucha en el puerto 8000.

## [Basheline] Generar CSV

### Primera importación (BBDD vacía)
Generar CSV compatible con HoMoDaba.
```bash
~ ./basheline/basheline.py -i BSLN_Input_Files* -o ./basheline/Listado_Pelis.csv
```
Siendo `BSLN_Input_Files*`:
 - Ficheros TXT resultado de ejecutar `find /media/bpk/ > BSLN_Input_Files-example.txt`  
  Basheline sólo considera los ficheros y carpetas multimedia que coinciden con el PATH regex  
  `/media/bpk/(HDD-(?:Pelis|Anime)-[0-9]{3})/([HS]D)`.  
  Por ejemplo `/media/bpk/HDD-Anime-001/HD/` o `/media/bpk/HDD-Pelis-010/SD/`.  
 - Ficheros CSV generados manualmente con los campos Localizacion, Título Original, Titulo traducido, Director, Año, Resolución y Formato.  
  Usar como referencia la siguiente estructura:  
  ```
  Localizacion;Título Original;Titulo traducido;Director;Año;Resolución;Formato
  Original;Black Swan;Cisne negro;Darren Aronofsky;2010;1080p;BLURAY
  ```

Tras generar el CSV con basheline, se puede importar en HoMoDaBa con el siguiente comando (definir el nivel de verbose al gusto):
```bash
~ ./import-csv.sh --csv-file ./basheline/Listado_Pelis.csv -v 2 
```
Nota: Esta operación puede tardar varias horas dependiendo del número de registros y la conexión a Internet.

Una vez haya terminado la importación, ya se podrá ver los resultados en la [página de HoMoDaBa](http://dominio.net:8000/homodaba/) (http://dominio.net:8000/homodaba/)

### Importaciones posteriores (BBDD con contenido)
<details>
  <summary>[TODO] basheline json files: HMDB_PATCH_JSON y HMDB_CSV2IMDB_JSON
  </summary>

```bash
~ ./basheline/basheline.py -i BSLN_Input_Files*.txt  -p "${HMDB_PATCH_JSON}" -m "${HMDB_CSV2IMDB_JSON}" -o /tmp/Listado_Pelis_corrected.csv
```
</details>


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


## Base de datos separada para la cache (generico)
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

## Base de datos separada para la cache (solo sqlite)
Podemos hacer algo mas sencillo si solo usamos sqlite como base de datos el proceso seria:
1. Parar todas las instancias que tengamos corriendo que esten usando la base datos
1. Migrar cambios ANTES de definir la variable CACHE_DATABASE:
   ```bash
   manage.sh migrate
   ```
1. Copiar la base de datos actual como la base de datos de cache:
   ```bash
   cd homodaba
   cp db.sqlite3 db-cache.sqlite3
   ls -lha *.sqlite3 # Para que veamos lo que encogen :P
   cd ..
   ```
1. Meter la variable nueva de entorno CACHE_DATABASE=1, donde tengas las variables de entorno en mi caso por ejemplo seria:
   ```bash
   echo "export CACHE_DATABASE=1" >> .venv
   ```
1. Borrar datos de cache de la base de datos "default" y datos en general de la base de datos "cache":
   ```bash
   manage.sh delete_cache --default-database
   manage.sh delete_all_movies --cache-database
   ```
1. (Opcionalmente) Muy recomendable limpiar las bases de datos de morralla temporal:
   ```bash
   cd homodaba
   sqlite3 db.sqlite3
   ```
   ```sqlite
   sqlite> VACUUM;
   ```
   ```bash
   sqlite3 db-cache.sqlite3
   ```
   ```sqlite
   sqlite> VACUUM;
   ```
   ```bash
   ls -lha *.sqlite3 # Para que veamos lo que encogen :P
   cd ..
   ```
1. Una vez hecho esto ya podemos arrancar de nuevo:
   ```bash
   start.sh
   ```

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
