#!/bin/bash
## start.sh [--rebuild] [--help]
##
## Descripcion:
##      Script para arrancar la aplicacion homodaba. De base no requiere mas que 
##      definir un SECRET_KEY en  "$VIRTUAL_ENV/env.sh" o en ".venv".
##      Ver "env.sh" para mas info.
##
## Argumentos:
##      --help, muestra esta ayuda y sale.
##      --rebuild, regenera el indice de ElasticSearch. Requiere que tengamos 
##          configuradas las variables ES_XXXXX en nuestro entorno.

source ./env.sh || exit 1

if [ "$1" == "--help" ]
then
    cat $0 | grep "^##"
    exit
fi

# Si tiene definida la config de ElasticSearch...
if [ "$ES_DSL_HOSTS" != "" ]; then
    # Comprueba si tenemos la imagen ya instalada aunque parada, de ser asi...
    if [ "$(docker ps -aq -f status=exited -f name=$ES_CONTAINER_NAME)" ]; then
        # Solo arrancamos la imagen
        docker start $ES_CONTAINER_NAME
    # Si no tenemos la imagen instalada
    elif [ ! "$(docker ps -q -f name=$ES_CONTAINER_NAME)" ]; then
        # Descargamos la imagen y la arrancamos
        docker pull $ES_CONTAINER_VERSION
        docker run --name $ES_CONTAINER_NAME -d -p 9200:9200 -p 9300:9300 -e "discovery.type=single-node" $ES_CONTAINER_VERSION
    fi

    # Si queremos hacer rebuild, tenemos que esperar a que termine de arrancar el ES
    if [ "$1" == "--rebuild" ]
    then
        # TODO: Para @bpk667, ya me he acordado porque esta este delay de 30 
        # segundos, el problema es que la imagen de elastic search se instala y
        # arranca rapido (diciendole a docker que esta ok), pero lo cierto es que
        # no ha terminado de arrancar hasta que pasa un rato... lo que tendriamos
        # que hacer es comprobar de alguna forma, con un bucle que haga llamadas 
        # a algun restful tontorron o algo por el estilo que tenga ES, y que nos
        # asegure que la imagen esta desplegada y el ES ha terminado de hacer 
        # sus mierdas del arranque...
        echo "Esperando a que termine de arrancar ElasticSearch..."
        sleep 30
        echo "Reconstruyendo indices ElasticSearch..."
        bash rebuild-es.sh
    fi
fi

if [ ! -e "homodaba/db.sqlite3" ]; then
    $DJANGO_MANAGE migrate
    $DJANGO_MANAGE createsuperuser
fi

$DJANGO_MANAGE runserver $LOCALNETIP:8000