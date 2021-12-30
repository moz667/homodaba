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

## FIXME: Problema con estaticos y gunicorn con DJANGO_DEBUG
## Si queremos usar gunicorn con DJANGO_DEBUG, tenemos que buscar una forma 
## alternativa de servir estaticos y aunque para eso montamos el proxy, no nos 
## interesa desde el punto de vista de tener watch de todos los estaticos... por
## eso por ahora vamos a dejarlo asin (si usas DJANGO_DEBUG, asumimos que no 
## sirves estaticos de otra forma)
if [ "$DJANGO_DEBUG" = "1" ] ; then
  echo ""
  echo "********************"
  echo "*** DJANGO_DEBUG ***"
  echo "********************"
  exec python manage.py runserver 0.0.0.0:8000
else
  exec gunicorn -b :8000 -w 4 homodaba.wsgi:application
fi