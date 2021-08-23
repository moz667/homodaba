#!/bin/sh

echo " * homodaba:trunk init *"

cd /opt/app/homodaba

# Checking SQL server is ready.
if [ "$DATABASE_ENGINE" = "mysql" ] ; then
  while true; do
    echo 'Waiting for SQL to be ready'
    if [ -z "$DATABASE_PASSWORD" ]; then
      mysqladmin -u"$DATABASE_USER" -h"$DATABASE_HOST" ping --silent
    else
      mysqladmin -u"$DATABASE_USER" -p"$DATABASE_PASSWORD" -h"$DATABASE_HOST" ping --silent
    fi
    
    if [ $? = 0 ]; then
      break
    fi
    sleep 1
  done
fi

python manage.py migrate
exec python manage.py runserver 0.0.0.0:8000
