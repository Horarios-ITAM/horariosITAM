import os
import itertools
import string
import time
import argparse
import logging
from typing import List, Iterator # Tuple removed

import utils

# Configuración básica de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BOLETIN_TEMPLATE_FILENAME = "boletinesTemplate.html"
HTML_LINK_PLACEHOLDER = "<!--Lista de links-->"
HTML_TIMESTAMP_PLACEHOLDER = "//Actualizado"
PDF_EXTENSION = ".pdf"

def generate_program_codes() -> Iterator[str]:
    """Genera posibles códigos de programa para la búsqueda por fuerza bruta."""
    # Combinaciones de 2 o 3 letras para la primera parte, y 1 letra para la segunda.
    # Ejemplos: AB-C, ABC-D
    for k_val in ['', *list(string.ascii_uppercase)]: # Tercera letra opcional
        product_iter = itertools.product(
            string.ascii_uppercase,  # Primera letra
            string.ascii_uppercase,  # Segunda letra
            [k_val],                 # Tercera letra (o vacía)
            string.ascii_uppercase   # Letra después del guion
        )
        for i, j, k, letra in product_iter:
            yield f'{i}{j}{k}-{letra}'


def fuerza_bruta(url_base_boletines: str, output_dir: str) -> None:
    """
    Intenta encontrar y descargar boletines por fuerza bruta.
    Prueba combinaciones de códigos de programa y descarga los PDF encontrados.
    Se recomienda usar muy infrecuentemente debido a la alta cantidad de peticiones.
    """
    logging.info("Iniciando búsqueda de boletines por fuerza bruta.")
    for programa_code in generate_program_codes():
        file_name = f"{programa_code}{PDF_EXTENSION}"
        download_url = f"{url_base_boletines}{file_name}"
        output_path = os.path.join(output_dir, file_name)

        logging.debug(f"Intentando descargar: {download_url}")
        try:
            # utils.descargaArchivo ahora usa verify_ssl=True por defecto.
            # Si hay problemas de SSL con escolar.itam.mx, se podría necesitar verify_ssl=False.
            # Por ahora, se asume que el certificado es válido o no es un problema.
            utils.descargaArchivo(output_path, download_url)
            logging.info(f"ÉXITO: {programa_code} encontrado y descargado en {output_path}")
        except utils.NetworkError as e:
            # Es esperado que muchos no se encuentren (404)
            if "404" in str(e): # Chequeo simple, podría ser más robusto si NetworkError tiene status_code
                logging.debug(f"No encontrado (404): {download_url} - {e}")
            else:
                logging.warning(f"No se pudo descargar {programa_code} desde {download_url}: {e}")
        except Exception as e: # Otras posibles excepciones no relacionadas a la red
            logging.error(f"Error inesperado descargando {programa_code} desde {download_url}: {e}")


def actualiza_ya_encontrados(url_base_boletines: str, boletines_dir: str) -> None:
    """
    Actualiza los boletines PDF existentes en `boletines_dir`
    intentando descargarlos de nuevo desde `url_base_boletines`.
    """
    logging.info(f"Iniciando actualización de boletines en: {boletines_dir}")
    if not os.path.isdir(boletines_dir):
        logging.warning(f"Directorio de boletines no encontrado: {boletines_dir}. No se puede actualizar.")
        return

    for fname in os.listdir(boletines_dir):
        if not fname.endswith(PDF_EXTENSION):
            continue
        
        logging.info(f"Intentando actualizar {fname}")
        download_url = f"{url_base_boletines}{fname}"
        output_path = os.path.join(boletines_dir, fname)
        try:
            utils.descargaArchivo(output_path, download_url)
            logging.info(f"Actualizado: {fname}")
        except utils.NetworkError as e:
            logging.warning(f"No se pudo actualizar {fname} desde {download_url}: {e}")
        except Exception as e:
            logging.error(f"Error inesperado actualizando {fname} desde {download_url}: {e}")


def agregaLinksDoc(boletines_dir: str) -> str:
    """
    Genera el HTML con links a los boletines PDF encontrados en `boletines_dir`,
    basado en una plantilla HTML.
    """
    logging.debug(f"Generando links HTML para boletines en: {boletines_dir}")
    sHTML_links = []
    if not os.path.isdir(boletines_dir):
        logging.warning(f"Directorio de boletines no encontrado: {boletines_dir}. No se generarán links.")
        return "" # O manejar de otra forma, e.g. retornar el template sin modificar

    # Usamos os.path.join para la ruta del template
    template_path = os.path.join(boletines_dir, BOLETIN_TEMPLATE_FILENAME)

    for fname in sorted(os.listdir(boletines_dir)):
        if not fname.endswith(PDF_EXTENSION):
            continue

        # La URL en el href debe ser relativa a la raíz del sitio, o como se sirva.
        # Si boletines.html está en la raíz, y los PDFs en 'assets/boletines/',
        # el link debería ser 'assets/boletines/archivo.pdf'.
        # El `base_dir` original en el href era `assets/boletines`.
        # Asumimos que `boletines_dir` es `assets/boletines` y los links son relativos a la raíz del sitio.
        link_path = f"{boletines_dir}/{fname}" # Manteniendo la estructura original del link
        program_name = fname.split(PDF_EXTENSION)[0]
        sHTML_links.append(f'<a href="{link_path}" target="_blank">{program_name}</a><br>')

    links_html_block = "\n".join(sHTML_links)

    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
    except FileNotFoundError:
        logging.error(f"Archivo de plantilla no encontrado: {template_path}")
        return f"Error: Plantilla no encontrada en {template_path}.<br>\n{links_html_block}" # Fallback
    except IOError as e:
        logging.error(f"Error leyendo archivo de plantilla {template_path}: {e}")
        return f"Error leyendo plantilla.<br>\n{links_html_block}" # Fallback

    return template_content.replace(HTML_LINK_PLACEHOLDER, links_html_block)

def agregarActualizadoTimestamp(html_content: str) -> str:
    """Reemplaza un placeholder en el HTML con el timestamp actual."""
    return html_content.replace(HTML_TIMESTAMP_PLACEHOLDER, str(time.time() * 1000))


def main():
    """Función principal para ejecutar el script."""
    parser = argparse.ArgumentParser(
        prog='Cache Boletines',
        description='Descarga/actualiza copias de los programas académicos (boletines) del ITAM.'
    )
    parser.add_argument(
        '--url_boletines',
        default='http://escolar.itam.mx/licenciaturas/boletines/',
        help='URL base donde se encuentran los boletines. Ej: "[url_boletines]/COM-H.pdf".'
    )
    parser.add_argument(
        '--modo',
        choices=['actualiza', 'encuentra', 'html'],
        default='actualiza',
        help=(
            'Modo de operación: '
            '"actualiza" (actualiza boletines existentes en --dir), '
            '"encuentra" (busca nuevos boletines por fuerza bruta y los guarda en --dir), '
            '"html" (solo actualiza el archivo boletines.html).'
        )
    )
    parser.add_argument(
        '--dir',
        default='assets/boletines',
        help='Directorio para guardar/leer los boletines descargados y donde se espera boletinesTemplate.html.'
    )
    parser.add_argument(
        '--output_html_file',
        default='boletines.html',
        help='Nombre del archivo HTML de salida que contendrá los links a los boletines.'
    )

    args = parser.parse_args()

    if args.modo == 'encuentra':
        logging.info(f"Modo 'encuentra': Obteniendo boletines por fuerza bruta desde {args.url_boletines}")
        fuerza_bruta(args.url_boletines, args.dir)
    elif args.modo == 'actualiza':
        logging.info(f"Modo 'actualiza': Actualizando boletines en {args.dir} desde {args.url_boletines}")
        actualiza_ya_encontrados(args.url_boletines, args.dir)
    
    # Siempre (re)generamos el HTML después de 'encuentra' o 'actualiza', o si modo es 'html'
    logging.info(f"Generando archivo HTML: {args.output_html_file}")
    html_con_links = agregaLinksDoc(args.dir)
    html_final = agregarActualizadoTimestamp(html_con_links)

    try:
        with open(args.output_html_file, 'w+', encoding='utf-8') as f:
            f.write(html_final)
        logging.info(f"Archivo HTML '{args.output_html_file}' generado/actualizado exitosamente.")
    except IOError as e:
        logging.error(f"No se pudo escribir el archivo HTML '{args.output_html_file}': {e}")

if __name__ == '__main__':
    main()