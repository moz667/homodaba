#!/bin/bash

MANAGE="python homodaba/manage.py"

if [ ! -e "homodaba/db.sqlite3" ]; then
    $MANAGE migrate
    $MANAGE createsuperuser
fi

$MANAGE runserver