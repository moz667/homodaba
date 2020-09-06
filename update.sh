#!/bin/bash
## update.sh [theme]
## theme, diseño en la admin, valores posibles:
##        django, DJANGO THEME
##        bootstrap, BOOTSTRAP THEME
##        foundation, FOUNDATION THEME
##        uswds, U.S. WEB DESIGN STANDARDS THEME
##    mas info: [https://pypi.org/project/django-admin-interface/]

AVAILABLE_THEMES="django bootstrap foundation uswds"
THEME=""

is_theme_available() {
    for value in $AVAILABLE_THEMES
    do
        if [ $THEME == $value ]
        then
            return 1
        fi
    done

    return 0
}

if [ "$1" == "--help" ]
then
    cat $0 | grep "^##"
    exit
elif [ "$1" != "" ]
then
    THEME="$1"
fi

if [ "$THEME" != "" ]
then
    is_theme_available
    IS_THEME_AVAILABLE=$?

    if [ "$IS_THEME_AVAILABLE" == "0" ]
    then
        echo "ERROR: Ese theme no esta disponible"
        cat $0 | grep "^##"
        exit
    fi
fi

MANAGE="python homodaba/manage.py"

$MANAGE migrate

if [ "$THEME" != "" ]
then
    $MANAGE loaddata admin_interface_theme_$THEME.json
    echo " * Recuerda que tienes que reiniciar el servicio para que se apliquen los cambios."
fi
