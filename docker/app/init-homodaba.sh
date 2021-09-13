#!/bin/sh -e

echo " * homodaba:trunk init *"

cd /opt/app/homodaba

# Checking if MySQL DB is ready.
if [ "$DATABASE_ENGINE" = "mysql" ] ; then
  if [ -n "$DATABASE_PASSWORD" ]; then
    PWD_PARAM="-p\"${DATABASE_PASSWORD}\""
  fi
  until \
    echo 'Waiting for SQL to be ready' && \
    mysqladmin -u"$DATABASE_USER" ${PWD_PARAM} -h"$DATABASE_HOST" ping --silent; do
      echo "mysqladmin -u$DATABASE_USER ${PWD_PARAM} -h$DATABASE_HOST ping --silent"
      sleep 1
    done
fi

python manage.py migrate

if [ "$CACHE_DATABASE" != '0' ]; then
  python manage.py migrate --database cache
fi

exec python manage.py runserver 0.0.0.0:8000
