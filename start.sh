#!/bin/bash -e

ENVFILE=".env"

DOCKER_COMPOSE="docker-compose"

if ! command -v $DOCKER_COMPOSE &> /dev/null
then
    DOCKER_COMPOSE="docker compose"
fi

# manage.py interactive (attach tty)
MANAGE="$DOCKER_COMPOSE exec app python homodaba/manage.py"
# manage.py NOT INTERACTIVE (Disable pseudo-tty allocation)
MANAGE_NOT_INT="$DOCKER_COMPOSE exec -T app python homodaba/manage.py"

generate_secret() {
    size=$1
    return "$(python3 -c "import secrets; print(secrets.token_urlsafe($size))")"
}

wait_until_healthy() {
	service="$1"
	
    container_id="$($DOCKER_COMPOSE ps -q "$service")"

    while true ; do 
        health_status="$(docker inspect -f "{{.State.Health.Status}}" "$container_id")"
        if [ "$health_status" == "healthy" ]; then
            echo "  - $service is ready"
            break
        fi
        echo "      * Waiting for $service to be ready..."
        sleep 5
    done
}

# Comprobamos que tiene docker
if ! command -v docker &> /dev/null; then
    echo "docker could not be found."
    echo "Read the manual and install it from https://docs.docker.com/desktop/"
    exit
fi

# Comprobamos que tiene $DOCKER_COMPOSE
if ! command -v $DOCKER_COMPOSE &> /dev/null; then
    echo "$DOCKER_COMPOSE could not be found."
    echo "Read the manual and install it from https://docs.docker.com/compose/install/"
    exit
fi

if [ ! -f $ENVFILE ]; then
    echo " - $ENVFILE not found, creating a new one."
    touch $ENVFILE
fi

if ! grep -q "^SECRET_KEY=\| *SECRET_KEY=" $ENVFILE; then 
    # Comprobamos que tiene python3 (solo es necesario si no tiene SECRET_KEY)
    if ! command -v python3 &> /dev/null; then
        echo "python3 could not be found."
        echo "Read the manual and install it from https://www.python.org/downloads/"
        echo "or alternatively generate a SECRET_KEY and store in $ENVFILE as:"
        echo "SECRET_KEY=<RANDOM LONG STRING>"
        exit
    fi

    echo " - SECRET_KEY not found in $ENVFILE, creating a new one."
    SECRET_KEY=`python3 -c "import secrets;print(secrets.token_urlsafe(37))"`
    echo "SECRET_KEY=$SECRET_KEY" >> $ENVFILE
fi

echo "Starting homodaba..."

# Esta comprobacion chusca. La he puesto para que evite arrancar static-build
# cada vez que se ejecute 
if [ ! -f static/build/css/main.thirdparty.css ]; then
    echo "  - building statics..."
    $DOCKER_COMPOSE run "static-build"
fi

echo "  - starting app..."
$DOCKER_COMPOSE up -d "app"

# 1) Esperar hasta que termine de arrancar el tema
wait_until_healthy "app"

# 2) Si no existe superuser en la bbdd pedimos para crearlo
superusers_count=`$MANAGE_NOT_INT shell -c "\
from django.contrib.auth import get_user_model;\
print(len(get_user_model().objects.filter(is_superuser=True).all()));\
"`

if [ "$superusers_count" == "0" ]; then
    echo ""
    echo "No superusers found. Do you want a new one? [Y/n]: "
    read create_superuser
    if [[ "$create_superuser" == "y" || "$create_superuser" == "Y" || "$create_superuser" == "" ]]; then
        $MANAGE createsuperuser
    fi
fi

# 3) Si no tiene datos damos opcion a importar demo-data
movies_count=`$MANAGE_NOT_INT shell -c "\
from data.models import Movie;\
print(len(Movie.objects.all()));\
"`

if [ "$movies_count" == "0" ]; then
    echo "No Movies. Do you want some sample data? [Y/n]: "
    read create_movies
    if [[ "$create_movies" == "y" || "$create_movies" == "Y" || "$create_movies" == "" ]]; then
        $MANAGE_NOT_INT import_csv --csv-file /opt/app/import/sample-data.csv -v 1
    fi
fi

# 4) Mostramos el resultado de la instalacion:
echo ""
echo " **************************************************************************"
echo " * Note that:                                                             *"
echo " *                                                                        *"
echo " *   - This is a test version, the stored data will be destroyed if it    *"
echo " *     remove the app container                                           *"
echo " *                                                                        *"
echo " *   - The script could have created a secret key for you and save it on  *"
echo " *     a .env file.                                                       *"
echo " *     This key is very important for the user authentication             *"
echo " *     If you delete and / or recreate it, this authentication will not   *"
echo " *     work.                                                              *"
echo " *                                                                        *"
echo " *   - To stop the app, execute:                                          *"
echo " *     # $DOCKER_COMPOSE stop                                              *"
echo " *                                                                        *"
echo " *   - To remove the app data, execute:                                   *"
echo " *     # $DOCKER_COMPOSE down                                              *"
echo " *                                                                        *"
echo " **************************************************************************"
echo ""
echo " - That's all!!!"
echo " - Visit http://127.0.0.1:8000/ for some fun."
echo ""
