#!/usr/bin/env bash

# Solo correr en el servidor.
# Script que corre el cron job para scrappear y hacer push a github.
# Siempre hacemos pull y aceptamos todos los cambios entrantes.

# NOTA: $1 = 'bruta' (sin comillas): se usa fuerza bruta para buscar boletines.

cd /home/horariosITAM;

git pull && git checkout --theirs . && python3 update/cacheBoletines.py $1 && git add . && git commit -m "auto update" && git push