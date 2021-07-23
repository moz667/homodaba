#!/bin/bash

echo " * homodaba:trunk init *"

cd /opt/app/homodaba/homodaba

python manage.py migrate
python manage.py runserver 0.0.0.0:8000
