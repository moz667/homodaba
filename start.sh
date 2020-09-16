#!/bin/bash

source ./env.sh || exit 1

if [ ! -e "homodaba/db.sqlite3" ]; then
    $DJANGO_MANAGE migrate
    $DJANGO_MANAGE createsuperuser
fi

$DJANGO_MANAGE runserver