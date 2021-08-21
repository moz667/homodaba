#!/bin/sh

echo " * homodaba:trunk init *"

cd /opt/app/homodaba

# Checking SQL server is ready.
if [ "$DATABASE_ENGINE" = "mysql" ] ; then
  while ! mysqladmin -u"$DATABASE_USER" -p"$DATABASE_PASSWORD" -h"$DATABASE_HOST" ping --silent ; do
    echo 'Waiting for SQL to be ready'
    sleep 1
  done
fi

python manage.py migrate
exec python manage.py runserver 0.0.0.0:8000
