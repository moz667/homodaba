#!/bin/bash

cd homodaba

MANAGE="python manage.py"

if [ ! -e "db.sqlite3" ]; then
    $MANAGE migrate
    $MANAGE createsuperuser
fi

$MANAGE runserver