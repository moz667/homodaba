#!/bin/bash

echo " * homodaba:trunk init *"

cd /opt/app/homodaba/homodaba

export SQLITE3_PATH="/opt/app/sqlite3"

python manage.py migrate
python manage.py runserver 0.0.0.0:8000
