#!/bin/bash -e

ENVFILE='.env'

generate_secret() {
    size=$1
    return "$(python3 -c "import secrets; print(secrets.token_urlsafe($size))")"
}

wait_until_healthy() {
	service="app"
	
    # FIXME: Ojo, esto es lo que fallaba el otro dia, si hay varios contenedores
    # que se asemejen (app es demasiado comun...) entonces container_id seria un MAP
    container_id="$(docker-compose ps -q "$service")"
    health_status="$(docker inspect -f "{{.State.Health.Status}}" "$container_id")"

    while [[ "$health_status" != "healthy" ]] ; do 
        echo 'Waiting for application to be ready'
        health_status="$(docker inspect -f "{{.State.Health.Status}}" "$container_id")"
        sleep 5
    done
}

COMPOSE_ARGS="--env-file $ENVFILE"

if [ ! -f $ENVFILE ]; then
    SECRET_KEY=generate_secret(37)
    COMPOSE_ARGS="-e SECRET_KEY"
fi

docker-compose $COMPOSE_ARGS up -d --build

# 1) Esperar hasta que termine de arrancar el tema
wait_until_healthy

# 2) Si no existe superuser en la bbdd pedimos para crearlo
check_superusers=$(cat <<EOF
from django.contrib.auth import get_user_model
print(len(get_user_model().objects.filter(is_superuser=True).all()))
EOF
)

# FIXME: idem que con el tema del map... (ver mas arriba)
django_manage="docker-compose exec -T app python homodaba/manage.py shell -c"

RETURN_CHECK_SUPERUSERS=`$django_manage $check_superusers`

if [ "$RETURN_CHECK_SUPERUSERS" == "0" ]; then
    echo 'No users. Created a new one:'
    $django_manage createsuperuser
fi

# 3) TODO: Si no tiene datos damos opcion a importar demo-data ??? por ahora TODO

# 4) Chequeamos:
#   - Si no tiene volumes (import sqlite) lo notificamos, import no es importante
#   - Si no tiene .env, notificamos SECRET_KEY
