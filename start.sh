#!/bin/bash

cd homodaba

MANAGE="python manage.py"

if [ ! -e "db.sqlite3" ]; then
    $MANAGE migrate
    $MANAGE createsuperuser
fi

# TODO: themes: https://pypi.org/project/django-admin-interface/
# DJANGO THEME (DEFAULT):
# Run python manage.py loaddata admin_interface_theme_django.json
# 
# BOOTSTRAP THEME:
# Run python manage.py loaddata admin_interface_theme_bootstrap.json
# 
# FOUNDATION THEME:
# Run python manage.py loaddata admin_interface_theme_foundation.json
# 
# U.S. WEB DESIGN STANDARDS THEME:
# Run python manage.py loaddata admin_interface_theme_uswds.json

$MANAGE runserver