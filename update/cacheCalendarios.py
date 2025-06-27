import time
import os
import logging
import argparse
from urllib.parse import urljoin
from typing import Dict, Any # Tuple removed, requests removed

# import requests # Keep requests for this specific initial fetch, or change to utils.getHTML -> No longer needed
from bs4 import BeautifulSoup

import utils

# --- Constants ---
DEFAULT_BASE_URL = 'https://escolar.itam.mx/servicios_escolares/servicios_calendarios.php'
DEFAULT_OUTPUT_DIR = 'assets/calendarios' # Used for saving downloaded files and finding template
DEFAULT_HTML_OUTPUT_FILE = 'calendarios.html'

TEMPLATE_FILENAME = "calendariosTemplate.html"
HTML_LINK_PLACEHOLDER = "<!--Lista de links-->"
HTML_TIMESTAMP_PLACEHOLDER = "//Actualizado"
HTML_LINK_CLASS = "linkCalendario" # class for the <a> tags in generated HTML
BS_LINK_CLASS = "enlace" # class for <a> tags to find in source HTML

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def generate_html_links_section(downloaded_files_info: Dict[str, Dict[str, str]], assets_prefix: str = "assets") -> str:
    """
    Generates the HTML block of links for the downloaded calendars.
    """
    html_links = []
    for text, link_info in downloaded_files_info.items():
        # urlCache is relative to the 'assets' dir, e.g., 'calendarios/file.pdf'
        # The final href should be relative to the site root, e.g. 'assets/calendarios/file.pdf'
        # Ensure assets_prefix does not end with / and urlCache does not start with /
        # or handle path joining more robustly.
        # Original: "assets/" + ligas["urlCache"]
        # Assuming urlCache is like "calendarios/file.pdf", so assets_prefix/ligas["urlCache"] -> "assets/calendarios/file.pdf"
        # If urlCache can be absolute or have '../', this needs care.
        # For now, assume urlCache is a path segment like 'calendarios/name.pdf'

        # Make sure we are constructing paths like 'assets/calendarios/doc.pdf'
        # where link_info['urlCache'] would be 'calendarios/doc.pdf'
        # The value of DEFAULT_OUTPUT_DIR ('assets/calendarios') is where files are saved.
        # The links in HTML should point to this location from the root of the website.
        # So, if urlCache is 'calendarios/file.pdf', the href becomes 'assets/calendarios/file.pdf'.
        # This means `assets_prefix` effectively is the parent of the `urlCache` path structure.
        # However, the original code was `assets/` + `hit['href']`. If `hit['href']` is `calendarios/file.pdf`,
        # then `assets/calendarios/file.pdf` is correct.
        # The key `urlCache` stores `hit['href']`.

        href_path = os.path.join(assets_prefix, link_info["urlCache"])
        # Normalize path for web (forward slashes)
        href_path = href_path.replace(os.sep, '/')

        html_links.append(
            f'<a href="{href_path}" class="{HTML_LINK_CLASS}" target="_blank">{text}</a><br>'
        )
    return "\n".join(html_links)


def apply_template(links_html_block: str, template_dir: str) -> str:
    """
    Reads the HTML template, replaces the placeholder with the generated links.
    """
    template_path = os.path.join(template_dir, TEMPLATE_FILENAME)
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
    except FileNotFoundError:
        logging.error(f"Archivo de plantilla no encontrado: {template_path}")
        return f"Error: Plantilla no encontrada en {template_path}.<br>\n{links_html_block}"
    except IOError as e:
        logging.error(f"Error leyendo archivo de plantilla {template_path}: {e}")
        return f"Error leyendo plantilla.<br>\n{links_html_block}"
    
    return template_content.replace(HTML_LINK_PLACEHOLDER, links_html_block)


def add_timestamp_to_html(html_content: str) -> str:
    """Replaces a timestamp placeholder in the HTML with the current time."""
    return html_content.replace(HTML_TIMESTAMP_PLACEHOLDER, str(time.time() * 1000))


def fetch_and_parse_source_page(source_url: str) -> BeautifulSoup:
    """Fetches the source page HTML and parses it with BeautifulSoup."""
    logging.info(f"Obteniendo HTML de: {source_url}")
    # Using utils.getHTML for robust fetching
    html_content = utils.getHTML(source_url) # SSL verify can be an issue with itam.mx
    return BeautifulSoup(html_content, "html.parser")


def download_calendar_files(soup: BeautifulSoup, source_url: str, output_dir: str) -> Dict[str, Dict[str, str]]:
    """
    Finds calendar links in the parsed HTML, downloads them, and returns their info.
    The output_dir is where files are saved, e.g., 'assets/calendarios'.
    The 'urlCache' in the returned dict will be relative to this output_dir's parent,
    e.g. 'calendarios/file.pdf' if output_dir is 'assets/calendarios'.
    """
    downloaded_files_info: Dict[str, Dict[str, str]] = {}
    links = soup.find_all("a", {"class": BS_LINK_CLASS})

    if not links:
        logging.warning(f"No se encontraron links con la clase '{BS_LINK_CLASS}' en {source_url}")

    for link_tag in links:
        link_text = link_tag.string
        raw_href = link_tag.get('href')

        if not link_text or not raw_href:
            logging.warning(f"Link saltado (texto o href vacío): {link_tag}")
            continue

        link_text = link_text.strip()
        # Ensure raw_href doesn't try to escape the intended directory (e.g. by starting with / or ..)
        # For simplicity, we assume hrefs are simple relative paths like 'calendarios/file.pdf'
        if raw_href.startswith("/") or ".." in raw_href:
            logging.warning(f"Link saltado (href potencialmente problemático '{raw_href}'): {link_text}")
            continue

        document_url = urljoin(source_url, raw_href)

        # Determine save path. Files are saved under output_dir.
        # e.g. if output_dir is 'assets/calendarios' and raw_href is 'calendarios/file.pdf',
        # then save_path is 'assets/calendarios/file.pdf'.
        # The original code used 'assets/' + hit['href'] which assumes hit['href'] is 'calendarios/...'
        # Let's ensure the raw_href itself determines the path within output_dir if it's structured that way,
        # or just use the filename part of raw_href.
        # If raw_href is 'calendarios/somefile.pdf', then os.path.basename(raw_href) is 'somefile.pdf'.
        # This means all files from different subpaths in href would save to the root of output_dir.
        # The original behavior: `utils.descargaArchivo('assets/' + hit['href'], urlDoc)`
        # If hit['href'] is 'LIC/calendarios/calesc2023.pdf', it saves to 'assets/LIC/calendarios/calesc2023.pdf'.
        # So, the path stored in `urlCache` should reflect this structure relative to `assets/`.

        # `raw_href` is like 'LIC/calendarios/calesc2023.pdf'.
        # `output_dir` is 'assets/calendarios'.
        # We want to save to 'assets/LIC/calendarios/calesc2023.pdf'.
        # This means the `output_dir` argument is more of a root for where these assets are stored.
        # Let's adjust: the true save path is effectively `assets_root_dir / raw_href`.
        # The `output_dir` passed ('assets/calendarios') seems to be the location of the template and final HTML.
        # This is a bit confusing. Let's assume `output_dir` is the actual directory to save into,
        # and `raw_href` might contain subdirectories.

        # If `raw_href` is `sub/file.pdf`, and `output_dir` is `assets/calendarios`,
        # then `save_path` becomes `assets/calendarios/sub/file.pdf`.
        # The `urlCache` for the HTML link construction needs to be `calendarios/sub/file.pdf`
        # if the `assets_prefix` in `generate_html_links_section` is `assets`.

        file_name_part = os.path.basename(raw_href) # e.g. calesc2023.pdf
        # save_path = os.path.join(output_dir, file_name_part) # This would lose subdirectories from href

        # Replicating original save logic: 'assets/' + hit['href']
        # Let's define an asset_root, assuming output_dir is 'assets/calendarios'
        # and hit['href'] might be 'calendarios/file.pdf' or 'lic/file.pdf' etc.
        # The `assets_prefix` for links is 'assets'.
        # `urlCache` should be `hit['href']` itself if it's already like 'calendarios/file.pdf'.
        save_path = os.path.join("assets", raw_href) # This matches original 'assets/' + hit['href']

        logging.info(f"Descargando '{link_text}' de {document_url} a {save_path}")
        try:
            utils.descargaArchivo(save_path, document_url)
            # urlCache should be raw_href, so that assets_prefix + urlCache = assets/raw_href
            downloaded_files_info[link_text] = {'urlCache': raw_href, 'urlITAM': document_url}
        except utils.NetworkError as e:
            logging.error(f"Fallo al descargar '{link_text}' de {document_url}: {e}")
        except Exception as e:
            logging.error(f"Error inesperado descargando '{link_text}': {e}")

    return downloaded_files_info


def main():
    """Función principal para ejecutar el script de cache de calendarios."""
    parser = argparse.ArgumentParser(
        description="Descarga y actualiza los calendarios académicos del ITAM."
    )
    parser.add_argument(
        '--source_url',
        default=DEFAULT_BASE_URL,
        help="URL de la página de calendarios del ITAM."
    )
    parser.add_argument(
        '--output_dir',
        default=DEFAULT_OUTPUT_DIR,
        help="Directorio base para guardar archivos descargados y encontrar la plantilla HTML. E.g., 'assets/calendarios'."
    )
    parser.add_argument(
        '--html_file',
        default=DEFAULT_HTML_OUTPUT_FILE,
        help="Archivo HTML de salida donde se guardarán los links. E.g., 'calendarios.html'."
    )
    # The assets_prefix is how links are formed in the final HTML, e.g. "assets" -> "assets/calendarios/file.pdf"
    # This might need to be an argument if 'assets' is not always the root for these files.
    # For now, it's hardcoded in generate_html_links_section.

    args = parser.parse_args()

    try:
        soup = fetch_and_parse_source_page(args.source_url)
    except utils.NetworkError as e:
        logging.error(f"No se pudo obtener la página principal de calendarios: {e}")
        return # Exit if main page fails

    # output_dir ('assets/calendarios') is where the template lives.
    # Downloaded files are saved relative to 'assets/' based on their href.
    downloaded_info = download_calendar_files(soup, args.source_url, args.output_dir)

    if not downloaded_info:
        logging.warning("No se descargaron archivos de calendario. El HTML no se actualizará con nuevos links.")
        # Still, we might want to regenerate the HTML with an empty list or existing files if any.
        # The current logic will create an empty link list if downloaded_info is empty.

    links_section_html = generate_html_links_section(downloaded_info, assets_prefix=os.path.dirname(args.output_dir))
    html_with_links = apply_template(links_section_html, args.output_dir) # template from output_dir
    final_html = add_timestamp_to_html(html_with_links)

    try:
        with open(args.html_file, 'w+', encoding='utf-8') as f:
            f.write(final_html)
        logging.info(f"Archivo HTML '{args.html_file}' generado/actualizado exitosamente.")
    except IOError as e:
        logging.error(f"No se pudo escribir el archivo HTML '{args.html_file}': {e}")


if __name__ == '__main__':
    main()
