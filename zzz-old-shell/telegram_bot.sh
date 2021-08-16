#!/bin/bash

source ./env.sh || exit 1

echo "Arrancando: homodaba/telegram_bot.py $*"
python homodaba/telegram_bot.py $*
