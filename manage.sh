#!/bin/bash

# Buscamos primero el contenedor de dev
CONTAINER_NAME=`docker ps -a|grep homodaba_dev-app|grep "Up "|sed -e "s/.* //g"`

# Si no encontramos ninguno, probamos con el NO-DEV
if [ -z "$CONTAINER_NAME" ]; then
    CONTAINER_NAME=`docker ps -a|grep homodaba-app|grep "Up "|sed -e "s/.* //g"`
fi

# Si todavia no hemos encontrado ninguno... probamos con regexp 
# es posible que tengamos alguno con otro sobrenombre
if [ -z "$CONTAINER_NAME" ]; then
    CONTAINER_NAME=`docker ps -a|grep "homodaba.*-app"|grep "Up "|sed -e "s/.* //g"`
fi

if [ -z "$CONTAINER_NAME" ]; then
    echo "No encuentro el contenedor de homodaba-app arrancado..."
    echo "Puedes arrancarlo de forma sencilla a traves de compose con:"
    echo "   # para entornos de produccion :"
    echo "   docker-compose up -d"
    echo "   # para entornos de desarrollo :"
    echo "   docker-compose -f docker-compose.dev.yml up"
else
    docker exec -it $CONTAINER_NAME python homodaba/manage.py $*
fi