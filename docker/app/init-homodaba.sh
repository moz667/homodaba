#!/bin/bash

echo " * homodaba:trunk init *"

cd /opt/app/homodaba

python manage.py migrate
exec python manage.py runserver 0.0.0.0:8000
