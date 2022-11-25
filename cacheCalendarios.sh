#!/usr/bin/env bash

# Solo correr en el servidor.
# Script que corre el cron job para scrappear y hacer push a github.
# Siempre hacemos pull y aceptamos todos los cambios entrantes.

cd /home/horariosITAM;

git pull && git checkout --theirs . && python3 update/cacheCalendarios.py && git add . && git commit -m "auto update" && git push