#!/bin/bash

MANAGE="python homodaba/manage.py"

if [ -z "$1" ]
then
    $MANAGE import_csv --help
    exit
fi

$MANAGE import_csv $*