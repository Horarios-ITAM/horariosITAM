#!/bin/bash

# Download required files only from repo
curl https://raw.githubusercontent.com/Horarios-ITAM/horariosITAM/master/proxy/abiertos.py > proxy.py
curl https://raw.githubusercontent.com/Horarios-ITAM/horariosITAM/master/update/utils.py > utils.py
curl https://raw.githubusercontent.com/Horarios-ITAM/horariosITAM/master/update/graceScrapper.py > graceScrapper.py

# Run the proxy server with uv
uv run abiertos.py