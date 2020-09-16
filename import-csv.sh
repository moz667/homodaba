#!/bin/bash

source ./env.sh || exit 1

if [ -z "$1" ]
then
    $DJANGO_MANAGE import_csv --help
    exit
fi

$DJANGO_MANAGE import_csv $*