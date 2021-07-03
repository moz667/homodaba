#!/bin/bash
## rebuild-es.sh [--rebuild]
## --rebuild, regenera el indice de ElasticSearch

source ./env.sh || exit 1

if [ "$1" == "--help" ]
then
    cat $0 | grep "^##"
    exit
fi

if [ "$(docker ps -aq -f status=exited -f name=$ES_CONTAINER_NAME)" ]; then
    docker start $ES_CONTAINER_NAME
elif [ ! "$(docker ps -q -f name=$ES_CONTAINER_NAME)" ]; then
    docker pull $ES_CONTAINER_VERSION
    docker run  --name $ES_CONTAINER_NAME -d -p 9200:9200 -p 9300:9300 -e "discovery.type=single-node" $ES_CONTAINER_VERSION
fi

# Si queremos hacer rebuild, tenemos que esperar a que termine de arrancar el ES
if [ "$1" == "--rebuild" ]
then
    echo "Esperando a que termine de arrancar ElasticSearch..."
    sleep 30
    echo "Reconstruyendo indices ElasticSearch..."
    bash rebuild-es.sh
fi

bash start.sh
