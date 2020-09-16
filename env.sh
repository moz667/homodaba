#!/bin/bash

export DJANGO_MANAGE="python homodaba/manage.py"

# Si queremos ElasticSearch, tenemos que especificar donde esta:
export ES_DSL_HOSTS="localhost:9200"

# y podemos ponerle nombre al contenedor docker:
export ES_CONTAINER_NAME="homodaba_es"
export ES_CONTAINER_VERSION="docker.elastic.co/elasticsearch/elasticsearch:7.9.1"