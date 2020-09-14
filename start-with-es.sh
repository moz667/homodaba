#!/bin/bash

export ES_DSL_HOSTS='localhost:9200'

docker pull docker.elastic.co/elasticsearch/elasticsearch:7.9.1
docker run  --name homodaba_es -d -p 9200:9200 -p 9300:9300 -e "discovery.type=single-node" docker.elastic.co/elasticsearch/elasticsearch:7.9.1

echo "Esperando a que termine de arrancar ElasticSearch"
sleep 30

python homodaba/manage.py search_index --rebuild

bash start.sh
