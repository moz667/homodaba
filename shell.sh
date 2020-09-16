#!/bin/bash

source ./env.sh || exit 1

$DJANGO_MANAGE shell
