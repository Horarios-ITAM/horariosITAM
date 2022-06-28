#!/usr/bin/env bash

python3 update/update.py && git add . && git commit -m "auto update" && git push