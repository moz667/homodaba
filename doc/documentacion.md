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
   CREATE DATABASE [DATABASE_NAME] CHARACTER SET utf8 COLLATE utf8_bin;
   ```
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
