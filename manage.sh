#!/bin/bash

source ./env.sh || exit 1

echo "Ejecutando: $DJANGO_MANAGE $*"
$DJANGO_MANAGE $*
