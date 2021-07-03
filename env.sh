#!/bin/bash

export DJANGO_MANAGE="python homodaba/manage.py"

# Si queremos ElasticSearch, tenemos que especificar donde esta:
export ES_DSL_HOSTS="localhost:9200"

# y podemos ponerle nombre al contenedor docker:
export ES_CONTAINER_NAME="homodaba_es"
export ES_CONTAINER_VERSION="docker.elastic.co/elasticsearch/elasticsearch:7.9.1"

# Ip donde escucha django
export LOCALNETIP='127.0.0.1'

# Ips que permitimos acceder a la escucha de django separadas por espacio
# https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
export ALLOWED_HOSTS='127.0.0.1'

if [ -e $VIRTUAL_ENV/env.sh ]; then
  source $VIRTUAL_ENV/env.sh
fi

if [ "$SECRET_KEY" == "" ]; then
    echo -e " * La variable SECRET_KEY es obligatoria * \n\
mas info: https://docs.djangoproject.com/en/dev/ref/settings/#secret-key\n\
Se puede definir esta variable dentro del archivo .venv de la forma:\n\n\
    export SECRET_KEY='XX_RANDOM_AND_WEIRD_STRING_XX'\n\n\
Tambien es posible sobreescribir otras variables definidas en env.sh tales\n\
como LOCALNETIP y ALLOWED_HOSTS."

    exit 1
fi
