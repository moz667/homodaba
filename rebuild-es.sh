#!/bin/bash

source ./env.sh || exit 1

$DJANGO_MANAGE search_index --rebuild
