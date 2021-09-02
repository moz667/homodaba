#!/bin/bash -e

# TODO: Chequear dependencias...
# Requisitos:
#   - docker
#   - docker-compose
#   - python3

ENVFILE=".env"
# TODO: Revisar... Esto no me acaba de convencer... para no mostrar el 
# WARNING de la contraseña de mysql solo he visto esta forma... Lo cual
# nos desactiva todos los mensajes que no sean ERROR del compose, por lo
# que tendremos que contar que esta haciendo en cada momento...
COMPOSE="docker-compose --log-level ERROR"
# manage.py interactive (attach tty)
MANAGE="$COMPOSE exec app python homodaba/manage.py"
# manage.py NOT INTERACTIVE (Disable pseudo-tty allocation)
MANAGE_NOT_INT="$COMPOSE exec -T app python homodaba/manage.py"

generate_secret() {
    size=$1
    return "$(python3 -c "import secrets; print(secrets.token_urlsafe($size))")"
}

wait_until_healthy() {
	service="$1"
	
    container_id="$($COMPOSE ps -q "$service")"

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

wait_until_finish() {
	service="$1"
	
    container_id="$($COMPOSE ps -q "$service")"

    while true ; do 
        status="$(docker inspect -f "{{.State.Status}}" "$container_id")"
        if [ "$status" == "exited" ]; then
            echo "  - $service is finished"
            break
        fi
        echo "      * Waiting for $service to be finished..."
        sleep 5
    done
}

if [ ! -f $ENVFILE ]; then
    SECRET_KEY=`python3 -c "import secrets;print(secrets.token_urlsafe(37))"`
    echo "SECRET_KEY=$SECRET_KEY" > $ENVFILE
fi

# TODO: Borrar todo este comentario una vez lo hable con @bpk667
# Esto es un comportamiento curiosos de compose...
# Cuando extiendes de otro compose, no detecta cambios
# en el Dockerfile del padre, por ello, para asegurarnos
# que detecta cambios en ello tendriamos que hacer algo asi:
# echo "Building app..."
# $COMPOSE -f docker-compose.base.yml build "app"
# Esta comentado ya que queremos mantenerlo lo mas simple posible :P

echo "Starting homodaba..."

# TODO: Esta comprobacion chusca. La he puesto para que evite arrancar static-build
# cada vez que se ejecute 
if [ ! -f static/build/css/main.thirdparty.css ]; then
    echo "  - building statics..."
    $COMPOSE up -d "static-build"
    wait_until_finish "static-build"
fi

echo "  - starting app..."
$COMPOSE up -d "app"

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
echo " *   - This is a test version, the stored data will be destroyed if it    *"
echo " *     remove the app container                                           *"
echo " *   - The script could have created a secret key for you and save it on  *"
echo " *     a .env file.                                                       *"
echo " *     This key is very important for the user authentication             *"
echo " *     If you delete and / or recreate it, this authentication will not   *"
echo " *     work.                                                              *"
echo " **************************************************************************"
echo ""
echo " - That's all!!!"
echo " - Visit http://127.0.0.1:8000/ for some fun."
echo ""
