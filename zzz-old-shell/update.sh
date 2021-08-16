#!/bin/bash
## update.sh [theme]
## theme, diseño en la admin, valores posibles:
##        django, DJANGO THEME
##        bootstrap, BOOTSTRAP THEME
##        foundation, FOUNDATION THEME
##        uswds, U.S. WEB DESIGN STANDARDS THEME
##    mas info: [https://pypi.org/project/django-admin-interface/]

source ./env.sh || exit 1

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
fi

pip install -r python-requirements.txt -q
$DJANGO_MANAGE migrate

if [ "$1" != "" ]
then
    THEME="$1"

    is_theme_available
    IS_THEME_AVAILABLE=$?

    if [ "$IS_THEME_AVAILABLE" == "0" ]
    then
        echo "ERROR: Ese theme no esta disponible, los themes disponibles son:"
        for theme in $AVAILABLE_THEMES
        do
            echo $theme
        done
        exit
    fi

    $DJANGO_MANAGE loaddata admin_interface_theme_$THEME.json
    echo " * Recuerda que tienes que reiniciar el servicio para que se apliquen los cambios."
fi