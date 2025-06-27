# Monitorea que el sitio funcione correctamente y notifica si algo esta raro
# Corrido con cronjob (ver .github/workflows/monitorea.yml)

import requests
import argparse
import time
import logging
import sys
import re # For robust parsing
from typing import Optional

from bs4 import BeautifulSoup
# Assuming utils.py might have DEFAULT_TIMEOUT, if not, define it here.
# from utils import DEFAULT_TIMEOUT # Not strictly needed if defining locally
DEFAULT_REQUEST_TIMEOUT = 10 # seconds

# Logger setup
logger = logging.getLogger(__name__)

# Global variable for ntfy.sh channel, set in main
NTFY_CHANNEL: Optional[str] = None

def notify_user(message: str, click_url: str, tags: str = "warning,horariositam") -> None:
    """Envia una notificación via ntfy.sh."""
    if not NTFY_CHANNEL:
        logger.critical("Canal de notificación (NTFY_CHANNEL) no configurado. No se puede notificar.")
        # Depending on severity, could exit, but for monitor, better to log and continue other checks if possible.
        return

    logger.info(f"Enviando notificación: '{message}' (URL: {click_url})")
    try:
        response = requests.post(
            f"https://ntfy.sh/{NTFY_CHANNEL}",
            data=message.encode('utf-8'), # ntfy expects bytes
            headers={
                "Click": click_url,
                "Tags": tags,
                "Title": "Alerta HorariosITAM" # Add a title
            },
            timeout=DEFAULT_REQUEST_TIMEOUT
        )
        response.raise_for_status() # Check for HTTP errors from ntfy.sh
        logger.debug(f"Notificación enviada exitosamente a ntfy.sh/{NTFY_CHANNEL}.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error enviando notificación a ntfy.sh: {e}")
    except Exception as e: # Catch any other unexpected error
        logger.error(f"Error inesperado durante el envío de notificación: {e}", exc_info=True)


def make_request(url: str, exit_on_error: bool = True) -> Optional[requests.Response]:
    """
    Realiza una petición GET a la URL dada.
    Notifica y opcionalmente termina el script si hay un error.
    """
    logger.debug(f"Realizando petición GET a: {url}")
    response: Optional[requests.Response] = None
    try:
        response = requests.get(url, timeout=DEFAULT_REQUEST_TIMEOUT)
        response.raise_for_status() # Levanta HTTPError para códigos 4xx/5xx
        logger.debug(f"Petición a {url} exitosa (Status: {response.status_code}).")
        return response
    except requests.exceptions.HTTPError as e:
        msg = f"Error HTTP {e.response.status_code} accediendo a {url}"
        logger.error(msg)
        notify_user(msg, url, tags="critical,horariositam") # HTTP errors are usually critical
        if exit_on_error:
            logger.critical("Terminando script debido a error HTTP.")
            sys.exit(1)
    except requests.exceptions.Timeout:
        msg = f"Timeout accediendo a {url}"
        logger.error(msg)
        notify_user(msg, url, tags="critical,horariositam")
        if exit_on_error:
            logger.critical("Terminando script debido a timeout.")
            sys.exit(1)
    except requests.exceptions.RequestException as e: # Other network errors (DNS, connection refused, etc.)
        msg = f"Error de red accediendo a {url}: {e}"
        logger.error(msg)
        notify_user(msg, url, tags="critical,horariositam")
        if exit_on_error:
            logger.critical("Terminando script debido a error de red.")
            sys.exit(1)
    return None # Return None if an error occurred and exit_on_error is False


def check_last_updated_time(file_url: str, max_days_old: int = 2) -> None:
    """
    Verifica la marca de tiempo 'actualizado' en un archivo JS y notifica si es muy antiguo.
    """
    logger.info(f"Verificando antigüedad del archivo: {file_url}")
    response = make_request(file_url, exit_on_error=False) # Don't exit immediately, check other files
    if response is None or not response.text:
        logger.warning(f"No se pudo obtener contenido de {file_url} para chequear antigüedad.")
        return

    file_name = file_url.split('/')[-1]

    # Intenta extraer la marca de tiempo de forma más robusta.
    # Asume formato: var actualizado = "1620000000000"; o var actualizado = 1620000000000;
    match = re.search(r"var\s+actualizado\s*=\s*['\"]?(\d+\.?\d*)['\"]?\s*;", response.text)

    if not match:
        msg = f"No se pudo encontrar la marca de tiempo 'actualizado' en {file_name}."
        logger.error(msg)
        notify_user(msg, file_url)
        return

    try:
        timestamp_str = match.group(1)
        timestamp_ms = float(timestamp_str)
        days_since_update = (time.time() - (timestamp_ms / 1000)) / (60 * 60 * 24)

        logger.info(f"Archivo {file_name} actualizado hace {days_since_update:.2f} días.")
        if days_since_update > max_days_old:
            msg = f"ALERTA: {file_name} fue actualizado hace {days_since_update:.2f} días (umbral: {max_days_old} días)."
            logger.warning(msg)
            notify_user(msg, file_url)
    except ValueError:
        msg = f"Error convirtiendo marca de tiempo '{timestamp_str}' a número en {file_name}."
        logger.error(msg)
        notify_user(msg, file_url)
    except Exception as e:
        msg = f"Error inesperado procesando marca de tiempo en {file_name}: {e}"
        logger.error(msg, exc_info=True)
        notify_user(msg, file_url)


def main():
    """Función principal del script de monitoreo."""
    global NTFY_CHANNEL # Allow modification of global variable

    parser = argparse.ArgumentParser(description="Monitorea el sitio HorariosITAM y envía notificaciones.")
    parser.add_argument('--url', help='URL base del sitio a monitorear.', default='https://horariositam.com')
    parser.add_argument('--channel', help='Canal de ntfy.sh para enviar notificaciones.', required=True)
    parser.add_argument('--max_data_age_days', type=int, default=2, help='Máxima antigüedad permitida para los archivos de datos (en días).')
    parser.add_argument('--log_level', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], help='Nivel de logging.')

    args = parser.parse_args()

    # Configure logger level from args
    logging.basicConfig(level=getattr(logging, args.log_level.upper()),
                        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
                        stream=sys.stdout) # Reconfigure to apply level and ensure it goes to stdout for Actions

    NTFY_CHANNEL = args.channel
    base_url = args.url.rstrip('/') # Asegurar que no haya / al final

    logger.info(f"==== Iniciando monitoreo para {base_url} ====")
    logger.info(f"Canal de notificación: ntfy.sh/{NTFY_CHANNEL}")
    logger.info(f"Antigüedad máxima de datos permitida: {args.max_data_age_days} días.")

    # 1. Chequear que el sitio base esté arriba
    logger.info(f"Verificando accesibilidad de la URL base: {base_url}")
    make_request(base_url, exit_on_error=True) # Salir si el sitio principal no está accesible

    # 2. Chequear antigüedad de los archivos de datos JS
    data_files_to_check = [
        f"{base_url}/js/datos/datos_index.js",
        f"{base_url}/js/datos/datos_profesores.js"
    ]
    for data_file_url in data_files_to_check:
        check_last_updated_time(data_file_url, args.max_data_age_days)

    # 3. Chequear página de calendarios y sus links
    calendarios_url = f"{base_url}/calendarios.html"
    logger.info(f"Verificando página de calendarios: {calendarios_url}")
    response_calendarios = make_request(calendarios_url, exit_on_error=False) # No salir si esta página falla, pero notificar

    if response_calendarios and response_calendarios.text:
        soup_calendarios = BeautifulSoup(response_calendarios.text, "html.parser")
        calendar_links = soup_calendarios.find_all("a", {"class": "linkCalendario"})

        if not calendar_links:
            msg = "No se encontraron links a calendarios (clase 'linkCalendario') en la página de calendarios."
            logger.warning(msg)
            notify_user(msg, calendarios_url)
        else:
            logger.info(f"Encontrados {len(calendar_links)} links de calendarios. Verificando accesibilidad...")
            for link_tag in calendar_links:
                href = link_tag.get('href')
                if not href:
                    logger.warning(f"Link de calendario sin href: {link_tag}")
                    continue

                # Los hrefs en calendarios.html son como 'assets/calendarios/calesc2024.pdf'
                # Se deben resolver relativos a la URL base.
                full_link_url = f"{base_url}/{href.lstrip('/')}"
                logger.debug(f"Verificando link de calendario: {full_link_url}")
                make_request(full_link_url, exit_on_error=False) # No salir en error de un solo link, pero notificar

    logger.info("==== Monitoreo finalizado ====")

if __name__ == '__main__':
    main()