#!/bin/bash

: <<EOF
DESCRIPCIÓN:
Fichero con los valores por defecto.
Para cambiarlos, se puede modificar directamente este fichero o los siguientes ficheros de configuración.
Ficheros de configuración:
  env.sh                            Este fichero con los valores por defecto que se actualiza cuando se actualiza el código.
  $VIRTUAL_ENV/env.sh               [OPCIONAL] Fichero de configuración si se utiliza un entorno virtual de Python.
  docker/.env ó docker/.env-no-es   [OPCIONAL] Fichero de configuración si se utiliza docker-compose.
  .venv                             Fichero oculto donde definir datos sensibles como SECRET_KEY o TBOT_TOKEN

PRECEDENCIA: .venv > docker/.env == docker/.env-no-es == VIRTUAL_ENV/env.sh > env.sh

Ejemplo para cambiar el valor de CACHE_DATABASE a 0:
echo "export CACHE_DATABASE=0" >> .venv
EOF

export DJANGO_MANAGE="python homodaba/manage.py"

# Si queremos ElasticSearch, tenemos que especificar donde está.
# Descomentar si se quiere usar ElasticSearch:
#export ES_DSL_HOSTS="localhost:9200"

# y podemos ponerle nombre al contenedor docker:
export ES_CONTAINER_NAME="homodaba_es"
export ES_CONTAINER_VERSION="docker.elastic.co/elasticsearch/elasticsearch:7.9.1"

# Ip donde escucha django
export LOCALNETIP='127.0.0.1'

# Variable que define los tipos validos de peliculas, por defecto solo movie,
# pero se podrian poner los que se quieran separandolos por comas:
# export IMDB_VALID_MOVIE_KINDS='movie,tv movie'

# Definimos que se use una base de datos distinta para Caché
export CACHE_DATABASE=1

# Ips que permitimos acceder a la escucha de django separadas por espacio
# https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
export ALLOWED_HOSTS='127.0.0.1'

# Mira primero en $VIRTUAL_ENV si existe un env.sh y lo importa
if [ -e $VIRTUAL_ENV/env.sh ]; then
    source $VIRTUAL_ENV/env.sh
fi

# Sobreescribe con lo que tengamos dentro de .venv (archivo oculto para que git)
# no lo pille
if [ -e .venv ]; then
    source .venv
fi


# Comprueba al final si tenemos definida la variable que no tiene valor 
# por defecto SECRET_KEY... de no tenerla tenemos que notificar y salirnos
if [ "$SECRET_KEY" == "" ]; then
  cat <<EOF
* La variable SECRET_KEY es obligatoria *
Mas info: https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
Se secomienda definir esta variable dentro del archivo .venv de la forma:

    echo "export SECRET_KEY='XX_RANDOM_AND_WEIRD_STRING_XX'" >> .venv

EOF
  exit 1
fi
