#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

PROJECT_DIR="/home/linuxuser/horariosProxy"
UV_EXEC="/home/linuxuser/.local/bin/uv"
APP_ENV="${APP_ENV:-production}"
ALLOWED_ORIGINS="${ALLOWED_ORIGINS:-https://horariositam.com,https://www.horariositam.com}"

# --- 1. Navigate to the project directory ---
cd "$PROJECT_DIR" || { echo "ERROR: Failed to change to project directory $PROJECT_DIR" >&2; exit 1; }
echo "[$(date)] Changed to directory: $PROJECT_DIR"
echo "[$(date)] Using APP_ENV=$APP_ENV"
echo "[$(date)] Using ALLOWED_ORIGINS=$ALLOWED_ORIGINS"

# --- 2. Download/Update Required Files ---
echo "[$(date)] Downloading/updating required files..."

# Ensure the parent directory for proxy.py is correct if it's not root
# For now, assuming all files go directly into PROJECT_DIR

curl -sL https://raw.githubusercontent.com/Horarios-ITAM/horariosITAM/master/proxy/abiertos.py -o abiertos.py || { echo "ERROR: Failed to download abiertos.py" >&2; exit 1; }
echo "Downloaded abiertos.py"

curl -sL https://raw.githubusercontent.com/Horarios-ITAM/horariosITAM/master/update/utils.py -o utils.py || { echo "ERROR: Failed to download utils.py" >&2; exit 1; }
echo "Downloaded utils.py"

curl -sL https://raw.githubusercontent.com/Horarios-ITAM/horariosITAM/master/update/graceScrapper.py -o graceScrapper.py || { echo "ERROR: Failed to download graceScrapper.py" >&2; exit 1; }
echo "Downloaded graceScrapper.py"

echo "[$(date)] All files downloaded successfully."

# --- 3. Run the proxy server with uv ---
echo "[$(date)] Starting proxy server with uv run..."

# Using 'exec' ensures that 'uv' replaces the shell script process
exec env APP_ENV="$APP_ENV" ALLOWED_ORIGINS="$ALLOWED_ORIGINS" "$UV_EXEC" run abiertos.py

# Commands after 'exec' will only run if 'uv' fails to start.
echo "ERROR: uv run command failed to start." >&2
exit 1



# /etc/systemd/system/horariosproxy.service

# [Unit]
# Description=Proxy para horariosITAM.com (grupos abiertos, etc)
# After=network.target

# [Service]
# User=linuxuser
# Group=linuxuser
# WorkingDirectory=/home/linuxuser/horariosProxy
# ExecStart=/home/linuxuser/horariosProxy/start_abiertos.sh
# Restart=always
# RestartSec=10
# StandardOutput=journal
# StandardError=journal

# [Install]
# WantedBy=multi-user.target
