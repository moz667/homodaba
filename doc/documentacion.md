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
